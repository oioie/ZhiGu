# Scrapy settings for erazor project
#
# DUPEFILTER_CLASS = 'scrapy_redis.dupefilter.RFPDupeFilter'
DUPEFILTER_CLASS = None
# DUPEFILDUPEFILTER_CLASSTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'

# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "erazor"

SPIDER_MODULES = ["erazor.spiders"]
NEWSPIDER_MODULE = "erazor.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "erazor (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
SCHEDULER = "erazor.engine.erazor_scheduler.erazorScheduler"
SCHEDULER_PERSIST = True
REDIS_START_URLS_ON_FLUSH = False
ITEM_PIPELINES = {
    'erazor.pipelines.mysql_pipeline.MysqlPipeline': 400,
}
# ENGINE = 'erazor.engine.erazorEngine'
MODE = "STRICT"  # DEBUG、STRICT、SIMPLE
QUEUE_PRIORITYS = [0, 1]
# REDIS_HOST = '192.168.56.131'
# REDIS_HOST = '192.168.110.200'
# REDIS_HOST = '127.0.0.1'

LOG_LEVEL = 'DEBUG'
MAX_WAIT_SIZE = 1000
MAX_ACK_TIME = 60
DOWNLOAD_DELAY = 1
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = '3306'
MYSQL_PASSWORD = '123456'
MYSQL_USER = 'root'
MYSQL_TABLE_NAME = 'reddit_post'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "erazor.middlewares.RedditSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "erazor.utils.retry.erazorRetryMiddleware": 543,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "erazor.pipelines.RedditPipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value

