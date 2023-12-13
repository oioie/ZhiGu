import json
import time
import typing

from scrapy_redis.connection import get_redis_from_settings
from redis import Redis

lua_scripts = """
local db_num = KEYS[3]
local set_key = KEYS[1] 
local lock_key = "Lock"..KEYS[1]
local run_key = KEYS[2]
local lock_timeout = ARGV[1]
local expire_time = ARGV[2]
local page_size = 10

redis.call('select', db_num)

if redis.call("set", lock_key, 1, "nx", "px", lock_timeout) then
  local cursor = '0' 
  local count = 0
  repeat
  
    local result = redis.call('sscan', set_key, cursor, 'COUNT', page_size)
    cursor = result[1]
    local members = result[2]

    for _,task_id in ipairs(members) do

      count = count + 1
      local score = redis.call('zscore', run_key, task_id)
      
      if not score then
        redis.call('zadd', run_key, expire_time, task_id)
        redis.call("del", lock_key)
        return task_id
      end
    end
  until cursor == '0' or count > 10

  redis.call("del", lock_key)

end

return nil
"""
undertaker_lua_scripts = ''' 
local hash_key = KEYS[1]
local db_num = KEYS[2]
local death_key = ARGV[1]
local task_id = ARGV[2]

redis.call('select', db_num)
local task_body = redis.call('HGET',hash_key, task_id)
if task_body then
        local s1 = redis.call('LPUSH', death_key, task_body)
        return s1
end
'''
edotensei_lua_scripts = '''
local death_key = KEYS[1]
local db_num = KEYS[2]
local hash_key = KEYS[3]
local set_key = KEYS[4]
local work_nums = ARGV[1]

redis.call('select', db_num)
local souls_nums = redis.call("LLEN", death_key)
if souls_nums > 0 then
    local count = 0
    local respawn_coins = (souls_nums/work_nums)*1.5
    while(count < respawn_coins)
    do
        count = count+1
        local soul = redis.call('LPOP', death_key)
        if soul then
            local body = cjson.decode(soul)
            local task_id = body["task_id"]
            body = nil
            local res = redis.call('SADD', set_key, task_id)
            if res then
                redis.call('HSET', hash_key, task_id, soul)
            end
        else
            break
        end
    end
end
'''
rulaishenzhang_lua_scripts = '''
local death_key = KEYS[1]
local db_num = KEYS[2]
local task_body = ARGV[1]

redis.call('select', db_num)
redis.call('LPUSH', death_key, task_body)
'''


def replace_priority(priority: int, key: str) -> str:
    if key.split('.')[-1].isdigit():
        ksp = key.split('.')
        ksp[-1] = str(priority)
        new_key = ".".join(ksp)
        return new_key
    else:
        new_key = f'{key}.{priority}'
        return new_key


def zip_key(func):
    def set_key(*args, **kwargs):
        self = args[0]
        if kwargs.get("priority") is not None:
            priority = kwargs["priority"]
        else:
            assert isinstance(args[1], int), "Priority must be a Int Type!"
            priority = args[1]
        base_task_hash = self.task_hash
        base_task_id_set = self.task_id_set
        base_running_zset = self.running_zset
        base_dead_queue = self.dead_queue

        self.task_hash = replace_priority(priority=priority, key=base_task_hash)
        self.task_id_set = replace_priority(priority=priority, key=base_task_id_set)
        self.running_zset = replace_priority(priority=priority, key=base_running_zset)
        self.dead_queue = replace_priority(priority=priority, key=base_dead_queue)

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = None
            print(e)
        self.task_hash = base_task_hash
        self.task_id_set = base_task_id_set
        self.running_zset = base_running_zset
        self.dead_queue = base_dead_queue
        return result

    return set_key


class BaseQueue:
    def __init__(self, **kwargs):
        if kwargs.get('server'):
            self.server = kwargs['server']
        else:
            self.server: Redis = get_redis_from_settings(settings=kwargs["settings"])
        self.name = kwargs["name"]
        self.settings = kwargs["settings"]
        self.base_key: str = f'{kwargs["name"]}.{kwargs["feed_id"]}.{kwargs["batch_id"]}@@'
        self.clear_flag_key: str = f'Clear.{self.base_key}flag'

    def encode_task(self, task):
        return json.loads(task).encode('utf-8')

    def decode_task(self, task):
        return json.dumps(task)


class TaskQueue(BaseQueue):
    def __init__(self, **kwargs):

        if kwargs.get("batch_id") is None:
            self.server: Redis = get_redis_from_settings(settings=kwargs["settings"])
            kwargs["batch_id"] = self.set_default_batch_id(feed_id=kwargs["feed_id"])
        self.current_feed_id = kwargs['feed_id']
        # kwargs['type'] = "Tq"

        super().__init__(**kwargs)
        self.task_hash = f"Th.{self.base_key}"

        # 任务id set
        self.task_id_set = f"Tis.{self.base_key}"

        # 真正执行执行的有序集合
        self.running_zset = f'Rs.{self.base_key}'

        # 失败任务的hash
        self.dead_queue = f"Dt.{self.base_key}"

        # 等待队列最大长度
        self.max_queue_size = kwargs["settings"]["MAX_WAIT_SIZE"]

        # 任务超时时间
        self.timeout = kwargs['settings']["MAX_ACK_TIME"]

    def set_default_batch_id(self, feed_id: str):
        key_list = self.get_keys_by_feed(feed_id=feed_id)
        _recent = {"batch_id": None, "time": 0}
        for key in key_list:
            batch_id = key.decode('utf-8').split('.')[-2].replace('@@', "")
            batch_time = int("".join([char for char in batch_id if char.isdecimal()]))
            if batch_time > _recent.get("time"):
                _recent["time"] = batch_time
                _recent["batch_id"] = batch_id

        return _recent["batch_id"] if _recent["batch_id"] else "Void"

    @zip_key
    def push(self, priority: int, task: dict):
        # task_hash = self.task_hash + f'.{priority}'
        # task_id_set = self.task_id_set + f'.{pririty}'
        task_id = task.get("task_id")
        pipeline = self.server.pipeline()
        pipeline.hset(self.task_hash, task_id, self.decode_task(task))
        pipeline.sadd(self.task_id_set, task_id)
        res = pipeline.execute()
        return res

    @zip_key
    def undertaker(self, priority: int, task_id: str):
        '''
        送葬者
        '''
        scripts = self.server.register_script(undertaker_lua_scripts)
        res = scripts(keys=[self.task_hash, 1], args=[self.dead_queue, task_id])
        if isinstance(res, int):
            if res > 0:
                self.remove(priority=priority, task_id=task_id)

    @zip_key
    def remove(self, priority: int, task_id: str):
        # task_hash = self.task_hash + f'.{priority}'
        # task_id_set = self.task_id_set + f'.{priority}'
        if self.server.sismember(self.task_id_set, task_id) is False:
            return
        pipeline = self.server.pipeline()
        pipeline.hdel(self.task_hash, task_id)
        pipeline.srem(self.task_id_set, task_id)
        pipeline.zrem(self.running_zset, task_id)
        pipeline.execute()

    @zip_key
    def pull(self, priority: int):
        # running_zset = self.running_zset + f'.{priority}'
        # task_hash = self.task_hash + f'.{priority}'
        # task_id_set = self.task_id_set + f'.{priority}'
        if self.server.zcard(self.running_zset) < self.max_queue_size:
            scripts = self.server.register_script(lua_scripts)
            expire_time = int(time.time() * 1000) + self.timeout * 1000
            id = scripts(keys=[self.task_id_set, self.running_zset, 1], args=['10', expire_time])
            if id:
                id = id.decode(encoding='utf-8')
                next_task = self.server.hget(self.task_hash, id)
                return json.loads(next_task)

    @zip_key
    def edotensei(self, priority: int, work_nums: int):
        '''
        えどてんせい
        穢土転生
        '''
        scripts = self.server.register_script(edotensei_lua_scripts)
        res = scripts(keys=[self.dead_queue, 1, self.task_hash, self.task_id_set], args=[work_nums])

    @zip_key
    def rulaishenzhang(self, priority: int, task_body: dict):
        '''
        死亡队列在task_hash 中 task已被释放时，处理死亡队列入队
        '''
        task_id = task_body.get("task_id")
        # 防止重复加入队列
        if self.server.hexists(self.task_hash, task_id):
            return
        scripts = self.server.register_script(rulaishenzhang_lua_scripts)
        res = scripts(keys=[self.dead_queue, 1], args=[json.dumps(task_body, ensure_ascii=False)])

    @zip_key
    def clear(self, priority: int) -> bool:
        clear_flag = self.server.get(self.clear_flag_key)
        if clear_flag:
            return False
        else:
            pipeline = self.server.pipeline()
            current_time = int(time.time() * 1000)
            pipeline.zremrangebyscore(self.running_zset, min=0, max=current_time)
            pipeline.execute()
            return True

    def set_clear_flag(self, expire: int):
        self.server.setex(self.clear_flag_key, expire, "OK")

    def get_keys_by_feed(self, feed_id: str):
        key_list = self.server.keys(f"*.{feed_id}.*")
        return key_list

    def get_task_queue_status(self) -> typing.Dict:
        status_table = []
        key_list = self.get_keys_by_feed(feed_id=self.current_feed_id)
        for key in key_list:
            key = key.decode("utf-8")
            if 'Tis' in key.split('.')[0]:
                size = self.server.scard(key)
            elif "Th" in key.split('.')[0]:
                size = self.server.hlen(key)
            elif 'Dt' in key.split('.')[0]:
                size = self.server.llen(key)
            elif 'Rs' in key.split('.')[0]:
                size = self.server.zcard(key)
            else:
                continue
            status_table.append({
                "name": key,
                "size": size,

            })
        return status_table

    def reset_base_key(self) -> bool:
        status_table = self.get_task_queue_status()
        for key in status_table:
            if 'Th.' in key.get("name"):
                new_batch_id = self.set_default_batch_id(feed_id=self.current_feed_id)
                self.__init__(
                    server=self.server,
                    batch_id=new_batch_id,
                    feed_id=self.current_feed_id,
                    name=self.name,
                    settings=self.settings
                )
                return True
        return False

