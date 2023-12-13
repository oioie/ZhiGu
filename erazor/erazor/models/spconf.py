from pydantic import EmailStr, BaseModel, field_validator
import typing
from erazor import models
import inspect

class SpiderConf(BaseModel):
    feed_id: typing.AnyStr
    path: typing.AnyStr
    worker_numbers: int
    email: typing.Union[None, EmailStr] = None
    max_ack_time: int
    max_retry_time: int
    awaken_cron_expression: typing.AnyStr
    save_table: typing.AnyStr
    mode: typing.AnyStr
    queue_prioritys: typing.List
    region: typing.Union[None, typing.AnyStr] = None
    save_model: typing.Union[None, str]

    @field_validator('save_model')
    def cls_contains_with_models(cls, value) -> str:
        """
        判断save_model 的类是否定义
        """
        if value is None:
            return None
        elif inspect.isclass(models.__dict__.get(value)):
            return value
        else:
            raise Exception(
                f"{models.__name__}.{value} does not exist"
            )
