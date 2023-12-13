import uuid
from datetime import datetime
from copy import deepcopy
import json


class SpiderTask:

    def __init__(self, priority=0, task_parent_id=None, priority_parent=0, task_id=None):
        generation_time = datetime.now()
        self.generation_time = str(generation_time)
        self.priority = priority
        self.parent_priority = priority_parent
        self.task_id = str(uuid.uuid1()) if task_id is None else task_id
        self.task_parent_id = task_parent_id
        self.generation_timestamp = str(int(generation_time.timestamp()*1000))
        self.task_body = None
        self.feed_id = None
        self.batch_id = None


    def to_json(self) -> dict:
        task_json = self.task_body
        if task_json.get('origin_task_id') is None:
            task_json["origin_info"] = self.gen_origin_info(self.task_body)
        return task_json

    def gen_task_body(self, task):
        self.task_body = deepcopy(task)
        self.feed_id = self.task_body.get("feed_id")
        self.batch_id = self.task_body.get("batch_id")
        # self.task_parent_id = task.get("task_parent_id")
        self.parent_priority = task.get("priority_parent", 0)
        if 'origin_task_id' not in task:
            self.origin_task_id = self.task_id
        else:
            self.origin_task_id = task.get("origin_task_id")
        self.task_body.update(
            generation_time=self.generation_time,
            priority=self.priority,
            task_id=self.task_id,
            task_parent_id=self.task_parent_id,
            priority_parent=self.parent_priority,
            generation_timestamp=self.generation_timestamp,
            origin_task_id=self.origin_task_id,
        )

    def gen_origin_info(self, task_json):
        return json.dumps(task_json)
