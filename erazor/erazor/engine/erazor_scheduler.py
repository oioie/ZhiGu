from scrapy_redis.scheduler import Scheduler
from scrapy_redis import defaults
from scrapy.utils.misc import load_object
from erazor.base.base_request import MyRequest
from erazor.queue.local_req_queue import RequestQueue
class erazorScheduler(Scheduler):

    def __init__(self, server,
                 persist=False,
                 flush_on_start=False,
                 queue_key=defaults.SCHEDULER_QUEUE_KEY,
                 queue_cls=defaults.SCHEDULER_QUEUE_CLASS,
                 dupefilter_key=defaults.SCHEDULER_DUPEFILTER_KEY,
                 dupefilter_cls=defaults.SCHEDULER_DUPEFILTER_CLASS,
                 idle_before_close=0,
                 serializer=None):
        super().__init__(server, persist, flush_on_start, queue_key, queue_cls, dupefilter_key, dupefilter_cls, idle_before_close, serializer)

    def enqueue_request(self, request):
        if not request.dont_filter and self.df.request_seen(request):
            self.df.log(request, self.spider)
            return False
        if self.stats:
            self.stats.inc_value('scheduler/enqueued/redis', spider=self.spider)
        self.queue.push(request)
        return True
    def __len__(self):
        return 1

    def next_request(self) -> MyRequest:
        block_pop_timeout = self.idle_before_close
        request = self.queue.pop(block_pop_timeout)
        if request is not None:
            if request.meta.get("task_body") is None:
                request.meta['task_body'] = self.spider.task.task_body
            return request
        task = self.spider.task_manager.pull_task(priority=0)
        # self.spider.logger.info("无任务")
        if task is not None:
            task["retry_time"] = 0
            task = self.spider.task_manager.assemble_task(task=task, priority=task.get("priority"))
        if request and self.stats:
            self.stats.inc_value('scheduler/dequeued/redis', spider=self.spider)
        return task

    def open(self, spider):
        '''
        根据爬虫信息生成指定的队列，dq 为死亡队列。tq 为任务队列。 wq 为等待队列, rq 为去重队列
        :param spider:
        :return:
        '''
        self.spider = spider


        try:
            self.queue = load_object(RequestQueue)(
                spider=spider,
                mode=spider.custom_settings['MODE'],
            )
        except TypeError as e:
            raise ValueError(f"Failed to instantiate queue class '{self.queue_cls}': {e}")

        self.df = load_object(self.dupefilter_cls).from_spider(spider)

        if self.flush_on_start:
            self.flush()
        # notice if there are requests already in the queue to resume the crawl
        if len(self.queue):
            spider.log(f"Resuming crawl ({len(self.queue)} requests scheduled)")