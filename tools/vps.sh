#!/bin/bash

XENHOME=/vps
XENSWAP=/swp
XENCONF=/etc/xen
XENLOG=/var/log/xen
XENTOOLLOG=/var/log/xen-tools

NAME=$1
VCPU=$2
VRAM=$3
SWAP=$4
DISK=$5
OS=$6
ADDRESS=$7
GATEWAY=$8
NETMASK=$9

genXenMac() {
    S="00:16:3e:"
    E=`(date; cat /proc/interrupts) | md5sum | sed -r 's/^(.{6}).*$/\1/; s/([0-9a-f]{2})/\1:/g; s/:$//;'`
    echo $S$E
}

freeram=`xentop -i 1 | grep 'free' | awk '{print $23}' | awk 'sub(".$", "")'`
freeram=$((freeram/1024))
askram=$((VRAM+16))
if [ $askram -gt $freeram ]
then
        echo "no free ram available"
        exit 1;
fi

if [ $OS == "centos6" ]
then
cat >$XENCONF/$NAME <<-__END__
bootloader = "/usr/bin/pygrub"
vcpus = "$VCPU"
maxmem = "$VRAM"
memory = "$VRAM"
name = "$NAME"
vif = [ "vifname=$NAME,mac=`genXenMac`,ip=$ADDRESS,rate=500KB/s,bridge=xenbr0" ]
disk = [ "file:$XENHOME/$NAME.img,xvda1,w","file:$XENSWAP/$NAME.swp,xvdb1,w" ]
#root = "/dev/sda1"
#extra = "fastboot"
on_shutdown = "destroy"
on_poweroff = "destroy"
on_reboot = "restart"
on_crash = "restart"
__END__
else
cat >$XENCONF/$NAME <<-__END__
bootloader = "/usr/bin/pygrub"
vcpus = "$VCPU"
maxmem = "$VRAM"
memory = "$VRAM"
name = "$NAME"
vif = [ "vifname=$NAME,mac=`genXenMac`,ip=$ADDRESS,bridge=xenbr0" ]
disk = [ "file:$XENHOME/$NAME.img,sda1,w","file:$XENSWAP/$NAME.swp,sda2,w" ]
root = "/dev/sda1"
extra = "fastboot"
on_shutdown = "destroy"
on_poweroff = "destroy"
on_reboot = "restart"
on_crash = "restart"
__END__
fi

if [ ! -f $XENHOME/$NAME.img ];
then
	dd if=/dev/zero of=$XENHOME/$NAME.img bs=1 count=1 seek=$DISK
	mkfs.ext3 $XENHOME/$NAME.img
	mount -o loop $XENHOME/$NAME.img /mnt
	tar -zxSf $XENHOME/$OS.tar.gz -C /mnt/
	umount /mnt
else
	echo $XENHOME/$NAME.img exists!;
	exit 1;
fi

if [ ! -f $XENHOME/$NAME.swp ];
then
	dd if=/dev/zero of=$XENSWAP/$NAME.swp bs=1024 count=`expr $SWAP \* 1024`
	mkswap $XENSWAP/$NAME.swp
fi

mount -o loop $XENHOME/$NAME.img /mnt

if [ $OS == "ubuntu" ] || [ $OS == "debian" ]
then
cat >/mnt/etc/network/interfaces <<-__END__
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet static
address $ADDRESS
gateway $GATEWAY
netmask $NETMASK
__END__
elif [ $OS == "centos5" ] || [ $OS == "fedora" ]
then
cat >/mnt/etc/sysconfig/network-scripts/ifcfg-eth0 <<-__END__
DEVICE=eth0
BOOTPROTO=none
ONBOOT=yes
TYPE=Ethernet
IPADDR=$ADDRESS
GATEWAY=$GATEWAY
NETMASK=$NETMASK
__END__
elif [ $OS == "centos6" ]
then
cat >/mnt/etc/sysconfig/network-scripts/ifcfg-eth0 <<-__END__
DEVICE="eth0"
BOOTPROTO="static"
DNS1="8.8.8.8"
GATEWAY="$GATEWAY"
IPADDR="$ADDRESS"
IPV6INIT="no"
MTU="1500"
NETMASK="$NETMASK"
NM_CONTROLLED="yes"
ONBOOT="yes"
TYPE="Ethernet"
__END__
elif [ $OS == "gentoo" ]
then
cat >/mnt/etc/conf.d/net <<-__END__
config_eth0="$ADDRESS netmask $NETMASK"
routes_eth0="default via $GATEWAY"
__END__
elif [ $OS == "arch" ]
then
cat >/mnt/etc/rc.conf <<-__END__
config_eth0="$ADDRESS netmask $NETMASK"
routes_eth0="default via $GATEWAY"

LOCALE="en_US.utf8"
HARDWARECLOCK="UTC"
USEDIRECTISA="no"
TIMEZONE="America/New_York"
KEYMAP="us"
CONSOLEFONT=
CONSOLEMAP=
USECOLOR="yes"
MOD_AUTOLOAD="yes"
MODULES=()
HOSTNAME="arch"
USELVM="no"
INTERFACES=(eth0)
eth0="eth0 $ADDRESS netmask $NETMASK"
gateway="default gw $GATEWAY"
ROUTES=(gateway)
DAEMONS=(syslog-ng network crond sshd)
__END__
fi

umount /mnt

xm create $NAME
