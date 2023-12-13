from erazor.base.task_manager import SpiderTaskManager
from erazor.queue.queue import TaskQueue
from erazor.utils._project import get_project_settings

from logging import getLogger
from load_config import load_spconf_by_feed_id

from scrapy.utils.misc import load_object
from scrapy.spiders import Spider
import random
import datetime
import time

logger = getLogger(__file__)


# spider.task_manager.task_queue = TaskQueue(name=self.spider.name,
#                                                 feed_id=task.feed_id,
#                                                 batch_id=task.batch_id,
#                                                 settings=self.spider.settings)
def generate_rand(a=32):
    b = ""
    hex_chars = "0123456789abcdefghijklmnopqrstuywxyz"
    for i in range(a):
        index = int(random.random() * 1e8) % len(hex_chars)
        random_char = hex_chars[index]
        b += random_char
    return b


def make_batch_id() -> str:
    rid = generate_rand(6)
    date_str = datetime.datetime.now().strftime('%Y%M%d%H%m%S')
    batch_id = f'test_{date_str}{rid}'
    return batch_id


def production_test_batch(feed_id: str):
    batch_id = make_batch_id()
    sp = load_spconf_by_feed_id(feed_id=feed_id)
    spider = compose_spider(sp, batch_id)
    keyword_list = [
        "apple", "huaiwei", "xiaomi",
        # "one plus", "vivo",
        # "somsong", "realme",
        # "redmi", "redmagic",
        # "nubia", "HTC",
        # "meizu", "IQOO",
        # "oppo", "SONY",
        "honor",
        "NOKIA"
    ]
    for key in keyword_list:
        task = {
            "url": None,
            "keyword": key,
            "feed_id": feed_id,
            "type": "comments",
            "date": str(int(time.time())),
            "status": "debug",
            "father_task_id": None,
            "batch_id": batch_id,
            "priority": 0,
            "region": "CA"

        }
        task = spider.task_manager.assemble_task(task=task)
        spider.task_manager.task_queue.push(
            priority=task.priority,
            task=task.to_json()
        )


def compose_spider(sp: str, batch_id: str) -> Spider:
    sp_cls = load_object(sp.get('PATH'))
    spider = sp_cls()
    spider.settings = get_project_settings()
    spider.custom_settings = sp
    spider.task_manager = SpiderTaskManager(logger=logger)
    spider.task_manager.task_queue = TaskQueue(name=spider.name,
                                               feed_id=sp.get("FEED_ID"),
                                               batch_id=batch_id,
                                               settings=spider.settings)
    return spider


if __name__ == '__main__':
    production_test_batch(feed_id='abc12345678')
