import json
import re
import time
from erazor.engine.erazor_crawler import CrawlerProcess
# from scrapy.utils.project import get_project_settings
from erazor.base.base_spider import BaseSpider
from erazor.base.spider_task import SpiderTask
from copy import deepcopy
from erazor.utils.load_config import load_spconf_by_feed_id
from hashlib import sha1

from erazor.utils._project import get_project_settings

class GoogleShopSpider(BaseSpider):

    name = "google_shop"
    allowed_domains = None
    start_urls = None
    redis_key = 'google:start_urls'
    region_map = {
    }
    headers = {
        "authority": "www.google.com",
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.google.com/preferences?hl=zh-CN&prev=https://www.google.com/search?q%3Dmake%26sca_esv%3D584961557&lang=1&prev=https://www.google.com/preferences?hl%3Dzh-CN%26prev%3Dhttps://www.google.com/search%253Fq%253Dmake%2526sca_esv%253D584961557",
        "sec-ch-ua": "\"Google Chrome\";v=\"119\", \"Chromium\";v=\"119\", \"Not?A_Brand\";v=\"24\"",
        "sec-ch-ua-arch": "\"x86\"",
        "sec-ch-ua-bitness": "\"64\"",
        "sec-ch-ua-full-version": "\"119.0.6045.160\"",
        "sec-ch-ua-full-version-list": "\"Google Chrome\";v=\"119.0.6045.160\", \"Chromium\";v=\"119.0.6045.160\", \"Not?A_Brand\";v=\"24.0.0.0\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": "\"\"",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-ch-ua-platform-version": "\"10.0.0\"",
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    task = {
        "url": None,
        "keyword": "Apple",
        "batch_id": "123",
        "feed_id": "google",
        "type": "comments",
        "date": str(int(time.time())),
        "status": "debug",
        "father_task_id": None,
        "feed_id": "123",
        "batch_id": "abc_20230807223031",
        "priority": 0,
        "region": "CA"

    }

    def start_task(self, task: SpiderTask):
        task_body = task.task_body
        # _keyword = task_body.get("keyword")
        if task_body.get("url"):
            _region = task_body.get("region")
            cookie = self.region_map.get(_region, {})
            _headers = self.headers.copy()
            _headers['Cookie'] = cookie
            yield self.Request(
                       url=task_body.get("url"),
                       method='GET',
                       headers=_headers,
                       dont_filter=True,
                       callback=self.parse_res,
                       meta={
                           "proxy": "http://127.0.0.1:7890"
                       })
            return
        url = f'https://www.google.com/preferences?lang=1'
        yield self.Request(url=url,
                           method='GET',
                           headers=self.headers,
                           dont_filter=True,
                           callback=self.init_region,
                           meta={
                               "proxy": "http://127.0.0.1:7890"
                           })


    def init_region(self, response):
        task_body = response.meta.get("task_body")
        _region = task_body.get("region")
        url = response.xpath('//div[@data-spbu]/@data-spbu').get()
        url = f'{url}&gl={_region}&noredirect=1'
        yield self.Request(url=url,
                           method='GET',
                           headers=self.headers,
                           dont_filter=True,
                           callback=self.set_region_cookie,
                           meta={
                               "proxy": "http://127.0.0.1:7890"
                           })

    def set_region_cookie(self, response):
        task_body = response.meta.get("task_body")
        keyword = task_body.get("keyword")
        set_cookie = response.headers.get('set-cookie', "")
        self.logger.info(f"Set-Cookie: <{set_cookie}>")
        yield self.Request(
            url=f'https://www.google.com/search?q={keyword}&sca_esv=584961557&psb=1&tbs=vw%3Ad&tbm=shop&start=0&sa=N&biw=1920&bih=489',
            method='GET',
            headers=self.headers,
            callback=self.parse_res,
            dont_filter=True,
            meta={
            "proxy": "http://127.0.0.1:7890"
        }
        )


    def parse_res(self, response):
        task_body = response.meta['task_body']
        _region = task_body.get('region')
        if self.region_map.get(_region, None) == None:
            self.region_map[_region] = response.request.headers.getlist('Cookie')[0].decode()

        raw_js = response.xpath('//div[@id="cnt"]/script[@nonce][2]').get()
        _pwc = re.findall("var _pmc=\'(.*?)';var", raw_js)[0]
        js_data = json.loads(_pwc.encode('utf-8').decode('unicode_escape')).get("spop", {}).get("r", {})
        rank = 0
        for k in js_data.keys():
            rank += 1
            _data = js_data.get(k)
            item = {
                "title": _data[34][0],
                "region": _data[34][5][0:2],
                "price": _data[34][5][3:],
                "price_symbol": _data[34][5][2],
                "url": _data[34][6],
                "abs_rank": rank,
                "from_url": response.url,
                "platform": "Google Shop",
                "unique_id": sha1((str(_data[34][6])+str(rank)).encode()).hexdigest()
            }
            self.logger.info(item)
            yield self.save_item(task_body=task_body, item=item)
        next_page = response.xpath('//a[@id="pnnext"]/@href').get()
        if next_page:
            new_task = deepcopy(task_body)
            new_task["url"] = f'https://www.google.com{next_page}'
            yield self.Task(priority=0, task=new_task)


if __name__ == '__main__':
    settings = get_project_settings()

    # 通过feed_id 加载 custom setting
    GoogleShopSpider.custom_settings = load_spconf_by_feed_id(feed_id='abc12345678')

    # 创建CrawlerProcess对象
    process = CrawlerProcess(settings)
    # 向CrawlerProcess对象添加您的爬虫类
    process.crawl(GoogleShopSpider)

    # 启动爬虫
    process.start()