# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import abc

from scrapy_redis.pipelines import RedisPipeline

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import logging
logger = logging.getLogger(__name__)
from scrapy_redis.pipelines import RedisPipeline
class basePipeline(metaclass=abc.ABCMeta):
    def __init__(self, table_name, dbpool):
        self.table_name = table_name
        self.dbpool = dbpool

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings, crawler.dbpool)

    @classmethod
    def from_settings(cls, settings, dbpool):
        params = {
            'table_name': settings['MYSQL_TABLE_NAME'],
            'dbpool': dbpool,
        }
        return cls(**params)

    @abc.abstractmethod
    def process_item(self, item, spider):
        spider.task_manager.release_task(priority=item['priority'], task_id=item['task_id'])
        return item

    def _process_item(self, item, spider):
        pass


    @abc.abstractmethod
    def install_data(self, tx, item):
        '''
        数据库插入
        '''


    @staticmethod
    @abc.abstractmethod
    def _handle_item_saved(rss, item, spider):

        '''
        入库成功
        '''


    @staticmethod
    @abc.abstractmethod
    def _handle_error(err, item, spider):

        '''
        入库失败
        '''
