#coding:utf-8
import _env
import sys
print sys.path
from model._db import redis
from saas.ttypes import  Task , Cmd
from array import array
from model.vps_sell import vps_one_list_by_vps_order, VpsOrder, VPS_STATE_PAY

REDIS_VPS_SAAS_CMD = 'VpsSaasCmd:%s'

def task_dumps(cmd, id):
    s = array('I')
    s.append(cmd)
    s.append(id)
    return s.tostring()

def _vps_saas_cmd_new(cmd , host_id , id):
    if not cmd:
        return
    r = task_dumps(cmd, id)
    key = REDIS_VPS_SAAS_CMD%host_id
    p = redis.pipeline()
    p.lrem(key, r)
    p.rpush(key, r)
    p.execute()

def task_loads(t):
    s = array('I')
    s.fromstring(t)
    return Task(*s)


def task_by_host_id(host_id):
    key = REDIS_VPS_SAAS_CMD%host_id
    t = redis.rpoplpush(key , key)
    if t:
        return task_loads(t)
    return Task()

def vps_saas_cmd_open(host_id, id):
    return _vps_saas_cmd_new(Cmd.OPEN, host_id, id)

def task_done(host_id, task):
    if not task.cmd:
        return
    s = task_dumps(task.cmd, task.id)
    redis.lrem(REDIS_VPS_SAAS_CMD%host_id, s)

if __name__ == '__main__':
    task = task_by_host_id(2)
    print task_done(2, task)
    print task
