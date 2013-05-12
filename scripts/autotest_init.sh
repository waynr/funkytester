#!/bin/sh

#-------------------------------------------------------------------------------
# Run standard setup commands to make available the absolute minimum set of
# services

mount -a

. /etc/default/rcS

/etc/init.d/sysfs.sh start
/etc/init.d/populate-volatile.sh start
/etc/init.d/networking start
/etc/init.d/modutils.sh start

/etc/init.d/ntpdate start
/etc/init.d/sshd start

ntpdate 192.168.2.1 0.pool.ntp.org


#-------------------------------------------------------------------------------
# Call python script that queries user for which test setup to use

# Prepare for dialog menus
#eval `busybox resize`
#export LANG="en_US.UTF-8"

# Call python script to choose test environment
cd /root/pytest

# TODO: distinguish between tests that run primarily on the UUT and those that
# only make xmlrpc calls and automated CLI commands to the UUT
#python /root/pytest/pytest_setup.py
    

#-------------------------------------------------------------------------------
# Addition services setup once /dev and pointercal are in place

hwclock -w 


#-------------------------------------------------------------------------------
# Run setup specific to the currently-selected testset

if [ -f ./current_test/init.sh ] ;then
	./current_test/init.sh
fi


#-------------------------------------------------------------------------------
# Provide "debug" shell if test exits

sh


#-------------------------------------------------------------------------------
# Fallback to default init process

exec /sbin/init
	
