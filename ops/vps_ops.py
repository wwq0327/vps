#!/usr/bin/env python

import _env
import conf
assert conf.MKFS_CMD

import os
import re
import time

import vps_common
from vps import XenVPS

from os_init import os_init

class VPSOps (object):

    def __init__ (self, logger):
        self.logger = logger

    def loginfo (self, vps, msg):
        message = "[%s] %s" % (vps.name, msg)
        if not self.logger:
            print message
        else:
            self.logger.info (message)

    def create_vps (self, vps):
        """ check resources, create vps, wait for ip reachable, check ssh loging and check swap of vps.
            on error raise Exception, the caller should log exception """
        assert isinstance (vps, XenVPS)
        assert vps.has_all_attr
        vps.check_resource_avail ()

        self.loginfo (vps, "begin to create image")
        vps_common.create_raw_image (vps.img_path, vps.disk_g, conf.MKFS_CMD, sparse=True)
        self.loginfo (vps, "image %s created" % (vps.img_path))
        
        if vps.swp_g > 0:
            vps_common.create_raw_image (vps.swp_path, vps.swp_g, "/sbin/mkswap")
            self.loginfo (vps, "swap image %s created" % (vps.swp_path))
        
        vps_mountpoint = vps_common.mount_loop_tmp (vps.img_path)
        self.loginfo (vps, "mounted vps image %s" % (vps.img_path))

        try:
            if re.match (r'.*\.img$', vps.template_image):
                vps_common.sync_img (vps_mountpoint, vps.template_image)
            else:
                vps_common.unpack_tarball (vps_mountpoint, vps.template_image)
            self.loginfo (vps, "synced vps os to %s" % (vps.img_path))
            
            self.loginfo (vps, "begin to init os")
            os_init (vps, vps_mountpoint)
            self.loginfo (vps, "done init os")
        finally:
            vps_common.umount_tmp (vps_mountpoint)
        xen_config = vps.gen_xenpv_config ()
        f = open (vps.config_path, 'w')
        try:
            f.write (xen_config)
        finally:
            f.close ()
        self.loginfo (vps, "%s created, going to start it" % (vps.config_path))
        vps.start ()
        if not vps.wait_until_reachable (60):
            raise Exception ("the vps started, seems not reachable")
        self.loginfo (vps, "started and reachable, wait for ssh connection")
        time.sleep (5)
        status, out, err = vps_common.call_cmd_via_ssh (vps.ip, user="root", password=vps.root_pw, cmd="free|grep Swap")
        self.loginfo (vps, "ssh login ok")
        vps.create_autolink ()
        self.loginfo (vps, "created link to xen auto")
        if status == 0:
            if vps.swp_g > 0:
                swap_size = int (out.split ()[1])
                if swap_size == 0:
                   raise Exception ("it seems swap has not properly configured, please check") 
                self.loginfo (vps, "checked swap size is %d" % (swap_size))
        else:
            raise Exception ("cmd 'free' on via returns %s %s" % (out, err))


    def delete_vps (self, vps):
        vps.stop ()
        self.loginfo (vps, "vps stopped, going to delete data")
        if os.path.exists (vps.img_path):
            os.remove (vps.img_path)
            self.loginfo (vps, "delete %s" % (vps.img_path))
        if os.path.exists (vps.swp_path):
            os.remove (vps.swp_path)
            self.loginfo (vps, "delete %s" % (vps.swp_path))
        if os.path.exists (vps.config_path):
            os.remove (vps.config_path)
            self.loginfo (vps, "delete %s" % (vps.config_path))
        if os.path.exists (vps.auto_config_path):
            os.remove (vps.auto_config_path)
            self.loginfo (vps, "delete %s" % (vps.auto_config_path))
        self.loginfo (vps, "deleted")


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
