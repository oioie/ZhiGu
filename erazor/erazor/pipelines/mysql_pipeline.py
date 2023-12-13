import logging
from .base_pipeline import basePipeline
from twisted.internet import defer
logger = logging.getLogger(__file__)
import traceback

class MysqlPipeline(basePipeline):
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

    # @defer.inlineCallbacks
    def process_item(self, item, spider):
        # if spider.custom_settings['MODE'] in ['DEBUG']:
        #     spider.task_manager.release_task(priority=item['priority'], task_id=item['task_id'])
        #     return item
        _table_name = spider.custom_settings["SAVE_TABLE"]
        query = self.dbpool.runInteraction(self.install_data, item, _table_name)
        query.addCallback(self._handle_item_saved, item, spider)
        query.addErrback(self._handle_error, item, spider)
        # yield query
        return query

    def _process_item(self, item, spider):
        pass


    def install_data(self, tx, item, _table_name):
        # sql = f'insert into {_table_name} (task_id, task_parent_id, origin_task_id, url, from_url, generation_timestamp, generation_time, feed_id, batch_id, spider_name, type, title, publish_time, platform, num_comments, unique_id) values (%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s,%s, %s)'
        # tx.execute(sql, (
        #     item["task_id"],
        #     item["task_parent_id"],
        #     item["origin_task_id"],
        #     item["url"],
        #     item["from_url"],
        #     item["generation_timestamp"],
        #     item["generation_time"],
        #     item["feed_id"],
        #     item["batch_id"],
        #     item["spider_name"],
        #     item["type"],
        #     item["title"],
        #     item["publish_time"],
        #     item["platform"],
        #     item["num_comments"],
        #     item["unique_id"]
        # ))

        # '%s,'* (len(item.keys()))
        # ",".join(list(item.keys()))
        #  s = "".join([f'item["{x}"],\n' for x in item.keys()])
        sql = f'insert into {_table_name} (task_id,task_parent_id,origin_task_id,url,from_url,generation_timestamp,generation_time,feed_id,batch_id,spider_name,type,title,platform,price,price_symbol,unique_id,abs_rank,region) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        tx.execute(
            sql,
            (
                item["task_id"],
                item["task_parent_id"],
                item["origin_task_id"],
                item["url"],
                item["from_url"],
                item["generation_timestamp"],
                item["generation_time"],
                item["feed_id"],
                item["batch_id"],
                item["spider_name"],
                item["type"],
                # item["priority"],
                item["title"],
                item["platform"],
                item["price"],
                item["price_symbol"],
                item["unique_id"],
                item["abs_rank"],
                item["region"],
            )
        )

    @staticmethod
    def _handle_item_saved(rss, item, spider):
        item['saved_count'] = 1

        # logger.info(f"Item stored in MySQL's DB:{item}")
        # 释放spiderTask
        # spider.task_manager.release_task(priority=item['priority'], task_id=item['task_id'])
        return item

    @staticmethod
    def _handle_error(err, item, spider):
        if 'Duplicate' in err.value.args[1]:
            logger.warning(f"已存储：{item['unique_id']}")
            item['saved_count'] = 1
            # spider.task_manager.release_task(priority=item['priority'], task_id=item['task_id'])
        else:
            traceback.print_exception(err.type, err.value, err.tb)
            item['save_failure_count'] = 1
        return item