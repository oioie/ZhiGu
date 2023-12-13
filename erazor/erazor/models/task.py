from pydantic import BaseModel, HttpUrl,PastDatetime
from typing import AnyStr, Union


class TaskModel(BaseModel):
    task_id: AnyStr
    task_parent_id: Union[AnyStr, None]
    origin_task_id: AnyStr
    url: HttpUrl
    from_url: Union[HttpUrl, None]
    generation_timestamp: AnyStr
    generation_time: AnyStr
    feed_id: AnyStr
    batch_id: AnyStr
    spider_name: AnyStr
    type: AnyStr
    priority: int = 0


class PostListModel(TaskModel):
    title: AnyStr
    publish_time: AnyStr
    platform: AnyStr
    num_comments: int
    unique_id: AnyStr
    abs_rank: int

    def __init__(self, **data):
        allowed = self.model_fields
        not_allowed = []
        for k in data.keys():
            if k not in allowed:
                not_allowed.append(k)
        for k in not_allowed:
            data.pop(k)

        super().__init__(**data)


class GoogleShopList(TaskModel):
    title: AnyStr
    platform: AnyStr
    price: AnyStr
    price_symbol: AnyStr
    unique_id: AnyStr
    abs_rank: int
    region: AnyStr

    def __init__(self, **data):
        allowed = self.model_fields
        not_allowed = []
        for k in data.keys():
            if k not in allowed:
                not_allowed.append(k)
        for k in not_allowed:
            data.pop(k)

        super().__init__(**data)
