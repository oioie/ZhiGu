import yaml
from typing import Dict
from pathlib import Path
from scrapy.spiders import Spider
from erazor.models import SpiderConf



def load_db_config() -> Dict:
    db_path = get_file_path() + '/configs/db.yaml'
    with open(db_path, mode='r', encoding='utf-8') as fp:
        db_conf = yaml.safe_load(fp)
        return dict((k.upper(), v) for k, v in db_conf.items())



def load_spider_config() -> Dict:
    _file = get_file_path() + '/configs/run.yaml'
    with open(_file, mode='r', encoding='utf-8') as fp:
        sp_conf = yaml.safe_load(fp)
        return sp_conf


def get_file_path():
    return Path.cwd().parent.as_posix()


def feed_id_by_spidercls(spider: Spider) -> list:
    sp_conf = load_spider_config()
    feed_list = []
    for sp in sp_conf:
        if sp.get("name") == spider.name:
            return feed_list.append(sp.get("feed_id"))


def load_spconf_by_feed_id(feed_id: str) -> Dict:
    '''
    通过feed_id 加载spider 配置
    '''
    sp_conf = load_spider_config()
    for sp in sp_conf:
        if sp.get("feed_id") == feed_id:
            sp = SpiderConf(**sp).model_dump(mode='json')
            return dict((k.upper(), v) for k, v in sp.items())


if __name__ == '__main__':
    # load_spider_config()
    load_db_config()
    # load_spconf_by_feed_id(feed_id='abc12345678')