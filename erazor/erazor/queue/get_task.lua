local db_num = KEYS[3]
local set_key = KEYS[1]
local lock_key = "Lock"..KEYS[1]
local run_key = KEYS[2]
local lock_timeout = ARGV[1]
local expire_time = ARGV[2]
redis.call('select', db_num)
if redis.call("set", lock_key, 1, "nx", "px", lock_timeout) then
    local num = 0
    while num<10 do
        num = num + 1
        local task_id = redis.call('srandmember', set_key)
        if task_id ~= false then
            local score = redis.call('zscore', run_key, task_id)
            if not score then
                redis.call('zadd', run_key, expire_time, task_id)
                redis.call("del", lock_key)
                return task_id
            end
        end
    end
    redis.call("del", lock_key)
end
return nil