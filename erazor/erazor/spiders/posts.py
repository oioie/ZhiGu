import time
from copy import deepcopy
from datetime import datetime

from erazor.base.base_spider import BaseSpider
from erazor.engine.erazor_crawler import CrawlerProcess
from erazor.utils.load_config import load_spconf_by_feed_id
from erazor.utils._project import get_project_settings


class PostsSpider(BaseSpider):
    name = "posts"
    allowed_domains = ["old.erazor.com"]
    start_urls = ["http://old.reddit.com/"]
    redis_key = 'reddit_post:start_urls'
    task = {
        "url": "https://old.reddit.com/top/?sort=top&t=hour",
        "batch_id": "123",
        "feed_id": "erazor",
        "type": "comments",
        "date": str(int(time.time())),
        "status": "debug",
        "father_task_id": None,
        "feed_id": "123",
        "batch_id": "abc_20230807223031",
        "priority": 0,

    }

    headers = {
        'Referer': 'https://old.reddit.com/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    def start_task(self, task):
        task_body = task.task_body
        url = task_body.get("url")
        yield self.Request(url=url, headers=self.headers, dont_filter=True, callback=self.parse,
                           meta={"proxy": "http://127.0.0.1:7890"})
        # yield self.Request(url=url, headers=self.headers, dont_filter=True, callback=self.parse, meta={"proxy":
        # "http://127.0.0.1:7890"}) yield self.Request(url=url, headers=self.headers,dont_filter=True,
        # callback=self.parse, meta={"proxy": "http://127.0.0.1:7890"})

    def parse(self, response):
        index = 0
        task = response.meta["task_body"]
        next_page = response.xpath("//span[@class='nextprev']/span[@class='next-button']/a/@href").get()
        for link in response.xpath('//div[@data-type="link"]'):
            index += 1
            # rank = link.xpath("span[@class='rank']")[0].text
            # if index > 3 and response.url != 'https://old.reddit.com/top/?sort=top&t=hour':
            #     raise ("解析失败")
            timestamp = int(link.xpath('@data-timestamp').get()) / 1000
            post_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
            title = link.xpath('div//p[@class="title"]/a/text()').get()
            # author = link.xpath('@data-author').get()
            # generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            original_id = link.xpath('@data-fullname').get()
            url = f"https://old.reddit.com{link.xpath('@data-permalink').get()}"
            num_comments = int(link.xpath('@data-comments-count').get())
            item = {
                "title": title,
                "publish_time": post_date,
                "url": url,
                "from_url": response.url,
                "num_comments": num_comments,
                "platform": "Reddit",
                "unique_id": original_id,
            }
            # self.logger.info(item)
            yield self.save_item(task_body=task, item=item)
        if next_page:
            new_task = deepcopy(task)
            new_task["url"] = next_page
            yield self.Task(task=new_task, priority=1)
        else:
            # yield self.Item
            pass

    # def parse(self, response):
    #     #第1步： 先做response正文的判断
    #
    #     #第2步： 从json 或者html中解析出后续的任务，或者需要保存的数据
    #
    #     #第3步: 入库数据
    #
    #     #第4步: 先队列发送后续的任务


if __name__ == '__main__':
    settings = get_project_settings()

    PostsSpider.custom_settings = load_spconf_by_feed_id(feed_id='abc987654321')

    # 创建CrawlerProcess对象
    process = CrawlerProcess(settings)
    # 向CrawlerProcess对象添加您的爬虫类
    process.crawl(PostsSpider)
    # 启动爬虫
    process.start()
