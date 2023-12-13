---
--- Generated by Luanalysis
--- Created by chaochao.
--- DateTime: 2023-11-19 14:41
---
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
