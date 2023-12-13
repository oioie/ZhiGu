import json
import time
import redis
# 任务最大重试次数
MAX_RETRIES = 3
from scrapy_redis.connection import get_redis_from_settings
class BaseQueue:
    def __init__(self, **kwargs):
        self.server = get_redis_from_settings(kwargs["spider"].settings)
        self.base_key = f'{kwargs["type"]}.{kwargs["spider"].name}.{kwargs["feed_id"]}.{kwargs["batch_id"]}_{kwargs["priority"]}'

    def encode_task(self, task):
        return json.loads(task).encode('utf-8')

    def decode_task(self, task):
        return json.dumps(task)
class TaskQueue(BaseQueue):

    def __init__(self, **kwargs):
        """初始化,连接redis"""
        super().__init__(**kwargs)
        # 任务hash
        self.task_hash = f"Th.{self.base_key}"

        # 任务id set
        self.task_id_set = f"Tis.{self.base_key}"

        # 等待执行的有序集合
        self.waiting_zset = f"Wt.{self.base_key}"

        self.running_stream = f'Rs.{self.base_key}'
        # 真正执行执行的有序集合

        # 失败任务的hash
        self.dead_queue = f"Dt.{self.base_key}"

        # 等待队列最大长度
        self.max_queue_size = kwargs["spider"].settings["MAX_WAIT_SIZE"]

        # 任务超时时间
        self.timeout = kwargs["spider"].settings["MAX_ACK_TIME"]

    def add_task(self):
        """添加任务"""
        if self.server.zcard(self.waiting_zset) >= self.max_queue_size:
            print("Queue is full.")
            return

        pipeline = self.server.pipeline()
        pipeline.hset(self.task_hash, task_id, content)
        pipeline.sadd(self.task_id_set, task_id)
        pipeline.execute()

    def get_task(self):
        """获取待执行任务"""
        # 从id set中一个id



    def finish_task(self, task_id):
        """完成任务"""
        pipeline = self.server.pipeline()
        pipeline.zrem(self.waiting_zset, task_id)
        pipeline.hdel(self.task_hash, task_id)
        pipeline.srem(self.task_id_set, task_id)
        pipeline.execute()

    def add_push_task(self, task_id, content):
        """推送任务"""
        content['push'] = True
        self.add_task(task_id, content)


    def retry_dead_task(self, task_id):
        """重试dead队列任务"""
        task = self.server.hget(self.dead_queue, task_id)
        if task['tries'] < MAX_RETRIES:
            self.add_task(task['id'], task['content'])
        else:
            # 移到dead队列
            self.server.srem(self.task_id_set, task['id'])
            self.server.hdel(self.task_hash, task['id'])
            self.server.hset(self.dead_queue, task['id'], task)
            self.server.expire(task['id'], 86400 * 3)

    def repush_dead_tasks(self):
        """重新推送dead队列任务"""
        for task_id in self.server.hkeys(self.dead_queue):
            task = self.server.hget(self.dead_queue, task_id)
            task['tries'] = 0
            self.add_task(task['id'], task['content'])
            self.server.hdel(self.dead_queue, task_id)