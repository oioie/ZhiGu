CREATE TABLE reddit_post (
unique_id VARCHAR(100) PRIMARY KEY,
task_id VARCHAR(100),
task_parent_id VARCHAR(100),
origin_task_id VARCHAR(100),
url TEXT,
from_url TEXT,
generation_timestamp BIGINT,
generation_time DATETIME,
feed_id VARCHAR(10),
batch_id VARCHAR(20),
spider_name VARCHAR(20),
type VARCHAR(20),
title TEXT,
publish_time DATETIME,
platform VARCHAR(20),
num_comments INT
);


CREATE TABLE google_shop (
unique_id VARCHAR(100) PRIMARY KEY,
task_id VARCHAR(100),
task_parent_id VARCHAR(100),
origin_task_id VARCHAR(100),
url TEXT,
from_url TEXT,
generation_timestamp BIGINT,
generation_time DATETIME,
feed_id VARCHAR(20),
batch_id VARCHAR(20),
spider_name VARCHAR(20),
type VARCHAR(20),
title TEXT,
platform VARCHAR(20),
region VARCHAR(20),
price_symbol VARCHAR(20),
price VARCHAR(20),
abs_rank INT
);