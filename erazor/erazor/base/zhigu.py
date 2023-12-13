from functools import wraps
from erazor.base.base_request import MyRequest
import traceback
from erazor.base.spider_task import SpiderTask
from erazor.utils.retry import get_retry_request


class RequestPrisonBreakError(Exception):

    def __init__(self, module_name):
        self.module_name = module_name

    def __str__(self):
        return f'{self.module_name} Attempting to break the shackles'


def brutal_zhigu(func):
    """
    ZhiGu: an shackles in ancient China.
    桎梏： 在足曰桎，在手曰梏。
    """



    @wraps(func)
    def inner(*args, **kwargs):
        self = args[0]
        args = args[1:]
        gen = func(*args, **kwargs)
        req_count = 0
        task_count = 0
        item_count = 0
        # 判断func 是否为MyRequest生成器
        next_req_id = None
        while True:
            try:
                if args[0] is None:
                    raise StopIteration("Args is None")
                item = next(gen)
                if isinstance(item, MyRequest):
                    req_count += 1
                    if req_count > 1:
                        self.logger.error("[Prophet][Anger]: This is we give you zhigu(shackles)!")
                        raise RequestPrisonBreakError(module_name=args[0].__module__)
                    else:
                        next_req_id = item.meta.get('req_id')
                        if isinstance(args[0], SpiderTask):
                            item.meta["task_body"] = args[0].to_json()
                        else:
                            item.meta["task_body"] = args[0].meta.get("task_body", {})
                        yield item
                elif isinstance(item, dict):
                    item_count += 1
                    if task_count > 1:
                        raise StopIteration(
                            "[Prophet][Warning]: "
                            "Dont do that！"
                            "Please standardize your parsing logic for keep terrifying things away from us forever")
                    yield item
                elif isinstance(item, SpiderTask):
                    task_count += 1
                    yield item
            except RequestPrisonBreakError as rpe:
                # 捕获 异常
                self.crawler.engine.close_spider(self, rpe.__str__())
                break
            except StopIteration as sp:

                if item_count > 0:
                    args[0].meta['all_items'] = item_count
                    if req_count > 0:
                        # 继续 记录
                        break
                    else:
                        # 检查是否为严格模式，释放请求链
                        if self.settings['MODE'] in ['STRICT']:
                            if args[0].meta.get('saved_count', 0) == item_count:
                                self.crawler.engine.slot.scheduler.queue.ack(args[0].meta.get("req_id"))
                                self.task_manager.release_task(
                                    priority=args[0].meta['task_body'].get('priority', 0),
                                    task_id=args[0].meta['task_body'].get('task_id', 0)
                                )
                            break
                        self.task_manager.release_task(
                            priority=args[0].meta['task_body'].get('priority', 0),
                            task_id=args[0].meta['task_body'].get('task_id', 0)
                        )
                        break
                else:
                    if req_count < 1:
                        # 解析函数什么都木有做.....
                        if task_count < 1:
                            self.logger.info("请检查解析函数是否出现了未能适配特殊请求")
                            break
                        else:
                            self.logger.info('[Prophet][puzzle]: Maybe not a good chioce.....')
                            self.crawler.engine.slot.scheduler.queue.ack(next_req_id)
                            self.task_manager.release_task(
                                priority=args[0].meta['task_body'].get('priority', 0),
                                task_id=args[0].meta['task_body'].get('task_id', 0)
                            )
                            break
                    else:
                        # 继续 记录， 并且释放请求链
                        self.crawler.engine.slot.scheduler.queue.ack(next_req_id)
                        break


            except Exception as e:

                # 解析错误，开始重试
                traceback.print_exc()
                if isinstance(args[0], SpiderTask):
                    self.logger.error("Please check Your start_task method!")
                    break
                max_retry_times = args[0].request.meta.get('max_retry_times', self.settings.getint('RETRY_TIMES'))
                priority_adjust = args[0].request.meta.get('priority_adjust',
                                                           self.settings.getint('RETRY_PRIORITY_ADJUST'))
                new_request = get_retry_request(request=args[0].request,
                                                spider=self,
                                                reason='解析错误',
                                                max_retry_times=max_retry_times,
                                                priority_adjust=priority_adjust,
                                                logger=self.logger,
                                                maybe_released=False
                                                )
                if new_request:
                    self.crawler.engine.slot.scheduler.enqueue_request(new_request)
                raise e

    return inner
    # return wrapper
