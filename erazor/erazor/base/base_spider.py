import scrapy

from erazor.base.task_manager import SpiderTaskManager
from erazor.base.spider_task import SpiderTask
import inspect
import types
from pydantic import ValidationError
import traceback
from erazor.base.base_request import MyRequest
from erazor.base.zhigu import brutal_zhigu
from scrapy.utils.misc import load_object

from erazor import models

# def generator_limiter(limit=1):

class BaseSpider(scrapy.Spider):
    name = "BaseSpider"

    def __init__(self):
        super().__init__()
        # self.schedule_periodic_task()
        self.Request = MyRequest
        self.task_manager = SpiderTaskManager(logger=self.logger)
        # 自动将spider类下所有生成器函数套上桎梏
        for name, method in inspect.getmembers(self, predicate=inspect.isgeneratorfunction):
            new_method = types.MethodType(brutal_zhigu(method), self)
            setattr(self, name, new_method)
        # 组装task
        self.task = self.task_manager.assemble_task(task=self.task, priority=self.task.get("priority"))


    def save_item(self, task_body: dict, item: dict)-> dict:
        new_item = task_body.copy()
        new_item.update(**item)
        new_item['spider_name'] = self.name
        model_cls = getattr(models, self.custom_settings.get("SAVE_MODEL"))
        try:
            new_item = model_cls(**new_item)
        except ValidationError as exc:
            self.logger.error(exc)
            return None
        return new_item.model_dump(mode='json')

    def Task(self, task, priority):
        new_task = self.task_manager.assemble_task(task=task, priority=priority)
        return new_task


    def start_task(self):
        pass




    # def schedule_periodic_task(self):
    #     def periodic_task():
    #         self.log('开始执行定时任务: ->', 1)
    #         pass
    #
    #     self.periodic_task = task.LoopingCall(periodic_task)
    #     self.start_task(3)

    # def Request(self, *args, **kwargs):
    #     self.logger.info(kwargs.get("meta"))
    #     yield MyRequest(*args, **kwargs)

    # @signals.connect(signals.close_spider)
    # def close_spider(self, spider):
    #     self.cron_scheduler.shutdown()
# do something