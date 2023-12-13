import logging
import time
from twisted.internet.task import LoopingCall
from twisted.internet.defer import Deferred, inlineCallbacks, succeed
from scrapy.core.engine import ExecutionEngine
from scrapy.utils.misc import load_object, create_instance
from typing import Callable, Iterable, Iterator, Optional, Set, Union
from scrapy.utils.log import logformatter_adapter, failure_to_exc_info
from scrapy.spiders import Spider
from scrapy.core.engine import Slot
from scrapy.utils.reactor import CallLaterOnce
from scrapy.http import Response, Request
from erazor.base.spider_task import SpiderTask
from erazor.engine.erazor_scraper import Scraper as MyScraper
from scrapy import signals

logger = logging.getLogger(__name__)


class Slot:
    def __init__(
            self,
            start_requests: Iterable,
            close_if_idle: bool,
            nextcall: CallLaterOnce,
            scheduler,
    ) -> None:
        self.closing: Optional[Deferred] = None
        self.inprogress: Set[Request] = set()
        self.start_requests: Optional[Iterator] = iter(start_requests)
        self.close_if_idle = close_if_idle
        self.nextcall = nextcall
        self.scheduler = scheduler
        self.heartbeat = LoopingCall(nextcall.schedule)

    def add_request(self, request: Request) -> None:
        self.inprogress.add(request)

    def remove_request(self, request: Request) -> None:
        self.inprogress.remove(request)
        self._maybe_fire_closing()

    def close(self) -> Deferred:
        self.closing = Deferred()
        self._maybe_fire_closing()
        return self.closing

    def _maybe_fire_closing(self) -> None:
        if self.closing is not None and not self.inprogress:
            if self.nextcall:
                self.nextcall.cancel()
                if self.heartbeat.running:
                    self.heartbeat.stop()
            self.closing.callback(None)


class erazorEngine(ExecutionEngine):

    def __init__(self, crawler, spider_closed_callback: Callable) -> None:
        self.crawler = crawler
        self.settings = crawler.settings
        self.signals = crawler.signals
        self.logformatter = crawler.logformatter
        self.slot: Optional[Slot] = None
        self.spider: Optional[Spider] = None
        self.running = False
        self.paused = False
        self.scheduler_cls = self._get_scheduler_class(crawler.settings)
        downloader_cls = load_object(self.settings['DOWNLOADER'])
        self.downloader = downloader_cls(crawler)
        self.scraper = MyScraper(crawler)
        self._spider_closed_callback = spider_closed_callback
        self.local_queue_count = 0
        self.task_queue_count = 0

    def _next_request_from_scheduler(self) -> Optional[Deferred]:
        assert self.slot is not None  # typing
        assert self.spider is not None  # typing

        request = self.slot.scheduler.next_request()
        if request is None:
            return None

        if isinstance(request, SpiderTask):
            request = self.load_task(request, self.spider)
            self.slot.scheduler.enqueue_request(request)
            return None

        d = self._download(request, self.spider)
        d.addBoth(self._handle_downloader_output, request)
        d.addErrback(lambda f: logger.info('Error while handling downloader output',
                                           exc_info=failure_to_exc_info(f),
                                           extra={'spider': self.spider}))
        d.addBoth(lambda _: self.slot.remove_request(request))
        d.addErrback(lambda f: logger.info('Error while removing request from slot',
                                           exc_info=failure_to_exc_info(f),
                                           extra={'spider': self.spider}))
        slot = self.slot
        d.addBoth(lambda _: slot.nextcall.schedule())
        d.addErrback(lambda f: logger.info('Error while scheduling new request',
                                           exc_info=failure_to_exc_info(f),
                                           extra={'spider': self.spider}))
        return d

    def load_task(self, task: dict, spider: Spider) -> Request:
        new_request = next(spider.start_task(task))
        # new_request.meta["task_body"] = task.task_body
        new_request.meta['is_begin'] = True
        return new_request

    @inlineCallbacks
    def open_spider(self, spider: Spider, start_requests: Iterable = (), close_if_idle: bool = True):
        if self.slot is not None:
            raise RuntimeError(f"No free spider slot when opening {spider.name!r}")
        logger.info("Spider opened", extra={'spider': spider})
        nextcall = CallLaterOnce(self._next_request)
        scheduler = create_instance(self.scheduler_cls, settings=None, crawler=self.crawler)
        start_requests = yield self.scraper.spidermw.process_start_requests(start_requests, spider)
        self.slot = Slot(start_requests, close_if_idle, nextcall, scheduler)
        self.spider = spider
        if hasattr(scheduler, "open"):
            yield scheduler.open(spider)
        yield self.scraper.open_spider(spider)
        self.crawler.stats.open_spider(spider)
        yield self.signals.send_catch_log_deferred(signals.spider_opened, spider=spider)
        self.slot.nextcall.schedule()
        self.slot.heartbeat.start(5)

    def _next_request(self) -> None:
        if self.slot is None:
            return

        assert self.spider is not None  # typing

        if self.paused:
            return None

        if self.check_all_queue():
            res = self.spider.task_manager.reset_batch()
            if res:
                self.task_queue_count = 0
            else:
                time.sleep(30)

        while not self._needs_backout() and self._next_request_from_scheduler() is not None:
            pass

        if self.slot.start_requests is not None and not self._needs_backout():
            try:
                request = next(self.slot.start_requests)
                request.meta['is_begin'] = True
            except StopIteration:
                self.slot.start_requests = None
            except Exception:
                self.slot.start_requests = None
                logger.error('Error while obtaining start requests', exc_info=True, extra={'spider': self.spider})
            else:
                self.crawl(request)

        if self.spider_is_idle() and self.slot.close_if_idle:
            self._spider_idle()

    def check_all_queue(self) -> bool:

        """
        检测队列情况策略：
        1. 先检查本地队列的大小是否为0，若为0 则queue_stat_count + 1，当queue_stat_count > 60 则记录queue_stat为休闲状态
        2. 当 queue_stat 为休闲的情况：检查task_queue的状态，若batch_status == [],记录
        """
        # if len(self.slot.scheduler.queue) == 0:
        #     self.local_queue_count += 1
        #     if self.local_queue_count > 5:
        #         self.local_queue_stat = True
        # else:
        #     self.local_queue_count = 0
        #     self.local_queue_stat = False
        #
        # if self.local_queue_stat:
        if not self.spider.task_manager.task_queue.get_keys_by_feed(feed_id=self.spider.custom_settings['FEED_ID']):
            self.task_queue_count += 1
            if self.task_queue_count > 10:
                return True
            else:
                return False
        else:
            self.task_queue_count = 0
