from pydantic import BaseModel, Field, HttpUrl
from typing import Union

class TaskModel(BaseModel):
    spider_name :str = Field()
    feed_id :str = Field()
    batch_id :str= Field()
    spider_type :str= Field()
    task_id :str = Field()
    task_parent_id: Union[str, None] = Field()
    task_origin_id :str = Field()
    genration_timestamp = Field()
    generation_time: str = Field()
    url: HttpUrl
    from_url = HttpUrl
