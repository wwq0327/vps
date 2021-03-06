#!/usr/bin/env python

import _env
from saas.ttypes import Cmd, Vps
import saas.VPS
from zkit.ip import ip2int, int2ip
import zthrift.server 
from zthrift.client import get_client
import unittest
import threading
import time
import logging
import conf

class DummyHandler (object):
    """ ignore the host_id, I'm just a test handler """

    def __init__ (self, queue_dict):
        assert isinstance (queue_dict, dict)
        self.queue_dict = queue_dict


    def todo (self, host_id, cmd):
        try:
             return self.queue_dict[cmd][0]
        except KeyError, e: # wrong cmd
            return -1
        except IndexError: # nothing in queue
            return 0

    def done (self, host_id, cmd, _id, state, message):
        try:
            self.queue_dict[cmd].remove (_id)
        except KeyError:
            pass

    def vps (self, vps_id):
        return Vps (id=vps_id, ipv4=ip2int ("10.10.1.%d" % (vps_id)), ipv4_netmask=ip2int ("255.255.255.0"), ipv4_gateway=ip2int ("10.10.1.1"),
                password="haha", os=50001, hd=50, ram=512, cpu=1, host_id=2)

def get_queue_dict ():
    queues = dict ()
    queues[Cmd.OPEN] = list ()
    queues[Cmd.REBOOT] = list ()
    queues[Cmd.CLOSE] = list ()
    return queues

def run_server (queue_dict):
#    server = zthrift.server.get_server_nonblock (saas.VPS, DummyHandler (queue_dict))
#    return server.serve ()
    zthrift.server.server (saas.VPS, DummyHandler (queue_dict), port=conf.SAAS_PORT + 1, allowed_ips=["119.254.32.166", "127.0.0.1"])
    print "server exit ?"


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    queue_dict = get_queue_dict ()
    th = threading.Thread(target=run_server, args=(queue_dict,))
    th.setDaemon(1)
    th.start ()
    time.sleep (2)
    transport, client = get_client (saas.VPS, host="127.0.0.1", port=conf.SAAS_PORT + 1)
    transport.open ()
    try:
        vps = client.vps (1) 
        print "id", vps.id, "os", vps.os, "cpu", vps.cpu, "ram", vps.ram, "hd", vps.hd, \
            "ip", int2ip (vps.ipv4), "netmask", int2ip (vps.ipv4_netmask), "gateway", int2ip (vps.ipv4_gateway), \
            "pw", vps.password
            
    finally:
        transport.close ()
#    unittest.main ()



# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
