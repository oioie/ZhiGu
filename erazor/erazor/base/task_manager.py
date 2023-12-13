import typing

from erazor.base.spider_task import SpiderTask
from erazor.queue.queue import TaskQueue
from apscheduler.schedulers.twisted import TwistedScheduler
from typing import Union
import uuid
import logging
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


class SpiderTaskManager:

    def __init__(self, **kwargs):
        self.task_queue: Union[None, TaskQueue] = None
        self.logger = kwargs['logger']
        # 添加周期调度器

    def register_cron_scheduler(self, interval_time: int = 360, cron_expression: str = '0/5 * * * *',
                                works_nums: int = 1, queue_prioritys: list = [0]):
        self.works_nums = works_nums
        self.queue_prioritys = queue_prioritys
        self.interval_time = interval_time + 10
        self.cron_scheduler = TwistedScheduler()
        scheduler_logger = logging.getLogger('apscheduler')
        scheduler_logger.setLevel(logging.WARNING)
        self.cron_scheduler.start()
        # 自动调度清理过期任务
        self.cron_scheduler.add_job(self.clean_expire_task, 'interval', seconds=interval_time)
        # 自动调度唤醒失败任务
        self.cron_scheduler.add_job(self.soul_shepherd, CronTrigger.from_crontab(cron_expression))
        # 自动调度检测任务批次状态
        # self.cron_scheduler.add_job(self.check_bacth_static, 'interval', seconds=5)

    def check_bacth_static(self):
        self.logger.info('正在检测当前批次的状态')


    def clean_expire_task(self):
        self.logger.info("[Ready]: 正在清理过期任务：")
        # try:
        #     self.logger.info("[Ready]: 正在清理过期任务：")
        #     for priority in self.queue_prioritys:
        #         self.logger.info(f'[Running]: 正在清理队列==>{priority}')
        #         res = self.task_queue.clear(priority=priority)
        #         if res is False:
        #             return
        #     self.task_queue.set_clear_flag(expire=self.interval_time)
        #     self.logger.info("[OK]: 过期任务清楚完成")
        # except Exception as e:
        #     self.logger.info(e)

    def release_task(self, priority: int, task_id: str):
        self.task_queue.remove(task_id=task_id, priority=priority)

    def death_notice(self, priority: int, task_id: str, task_body: Union[dict, None] = None):
        # 死亡宣告
        # pass
        if task_body:
            self.task_queue.rulaishenzhang(priority, task_body)
        else:
            self.task_queue.undertaker(priority=priority, task_id=task_id)

    @staticmethod
    def assemble_task(**kwargs) -> SpiderTask:
        task = kwargs.get("task")
        assert task is not None, 'Task 不能为空'
        assert task.get('feed_id') is not None, "feed_id 不能为空"
        assert task.get("batch_id") is not None, "batch_id 不能为空"
        assert task.get('priority') is not None, "priority 不能为空"
        spider_task = SpiderTask(task_parent_id=task.get("task_parent_id"), task_id=task.get("task_id"),
                                 priority=task.get("priority"))
        spider_task.gen_task_body(task)
        return spider_task

    def push_task(self, priority: int, task: SpiderTask) -> None:
        # 推送task
        generation_time = datetime.now()
        task.task_body.update(
            generation_time=str(generation_time),
            priority=priority,
            task_id=str(uuid.uuid1()),
            task_parent_id=task.task_id,
            priority_parent=task.priority,
            generation_timestamp=str(int(generation_time.timestamp() * 1000)),
            origin_task_id=task.origin_task_id,
        )
        signal = self.task_queue.push(priority=priority, task=task.to_json())
        # if signal and task.task_parent_id is not None:
        #     # 如果task 推送成功，则释放父任务
        #     parent_priority = task.parent_priority
        # 05daf488-8161-11ee-92bb-00e04c834d61
        #
        #     self.release_task(task_id=task.task_parent_id, priority=parent_priority)
        # else:
        #     pass

    def pull_task(self, priority: int) -> dict:
        return self.task_queue.pull(priority=priority)

    def close(self):
        pass

    def soul_shepherd(self):
        '''
        牧魂人
        '''
        for priority in self.queue_prioritys:
            self.logger.info(f"[牧魂人][Runnging]: 正在执行唤醒任务-----权重==>:[{priority}]")
            self.task_queue.edotensei(priority=priority, work_nums=self.works_nums)
            self.logger.info(f"[牧魂人][OK]: 已经唤醒任务-----权重==>:[{priority}]")

    def get_first_task(self):
        task = self.task_queue.pull(0)
        return task

    def get_batch(self) -> typing.Dict:
        return self.task_queue.get_task_queue_status()


    def reset_batch(self):
        res = self.task_queue.reset_base_key()
        if res:
            self.logger.info("batch 已经重置成功！")
            return True