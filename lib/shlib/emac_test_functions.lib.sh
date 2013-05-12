#!/bin/bash 

# utility functions

function log_error() {
	local ERR_CODE="${1:--2}"
	local FUNC_TYPE="${2:-unknown}"
	local DATE="$(date -Iseconds)"
	# ISO-8601 compliant date string with seconds precision

	if [ "${3}x" != "x" ] ;then
		EXTRA_INFO="${LOG_FILE_FS}${3}"
	fi

	if [ $ERR_CODE -eq -2 ] ;then
		echo "NOTE: Bad error code." >> $LOG_FILE
		return
	fi

	if [ ! -f $LOG_FILE ] ;then
		touch $LOG_FILE	
	fi

    LOG=""

	LOG+="${MAC}"
	LOG+="${LOG_FILE_FS}" 

	LOG+="${FUNC_TYPE}"
	LOG+="${LOG_FILE_FS}" 

	LOG+="${DATE}"
	LOG+="${LOG_FILE_FS}" 

	LOG+="${ERR_CODE}"
	#LOG+="${LOG_FILE_FS}"

	LOG+="${EXTRA_INFO}" 

	echo "${LOG}" >> $LOG_FILE
}

# moved util_source_resize definition; sourced here for compatibility reasons
source lib/util/common.lib.sh

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function source_resize_script() {
		util_source_resize $@
	}


# Network device testing functions

function test_template() {
	local FUNC_TYPE="XXX-XX"
	local ERR_CODE=0
	local EXTRA_INFO

	$TEST_BIN some_internal_function arg1 arg2
	
	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE " "
}

function test_mem() {
	local FUNC_TYPE="017-01"
	local ERR_CODE=0
	local EXTRA_INFO

    local free_KB=$(free | awk '/Mem:/ {print $4}')

    # only use 95% of the free memory
    local test_MB=$(( (${free_KB}/1024) * 19 / 20))

    memtester ${test_MB}
    
	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE " "
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function lshal_ethernet_test() {
		test_ethernet_lshal $@
	}

function test_ethernet_lshal() {
	local FUNC_TYPE="001-01"
	local ERR_CODE=0
	local USAGE=$(cat <<!!
ethernet_test <NUMBER_OF_INTERFACES>\n
!!
)
	local test_interfaces=" "
	local tmp

	local sysfs_dev_paths="$($LSHAL | awk -F\' '/^\ \ linux.sysfs_path.*eth./ { printf " %s",$2  }')"
	[ "x$1" != "x" ] && PING_DESTINATION=$1

	echo -e -n "Ethernet Device Test: \t\t\t\t" 
	
	if [ "x$sysfs_dev_paths" == "x" ] ;then
		echo -e "FAIL,\nEthernet, sysfs paths missing, " \
		"is the hardware detected?" 
		ERR_CODE=321

		log_error $ERR_CODE $FUNC_TYPE " "
		return
	fi

	for path in $sysfs_dev_paths ;do
	
		tmp=$(cat "$path/operstate")

		if [ "$tmp" == "up" ] || [ "$tmp" == "unknown" ] ;then
			test_interfaces+="$(awk -F\= '$1 == "INTERFACE" { print $2 } ' $path/uevent ) "
		
			# only check the link speed if the interface is up,
			# otherwise the speed will show up as 65536
			tmp=$(cat "$path/speed")
	
			if [ "x$tmp" != "x1000" ] ;then
				echo -e "FAIL,\nEthernet, link speed: " \
					"$tmp. Should be 1000. Check " \
					"for cold solder joints." 
				ERR_CODE=322

				log_error $ERR_CODE $FUNC_TYPE " "
				return
			fi
		fi
		
	done

	if [ "x$test_interfaces" == "x" ] ;then
		echo -e "FAIL,\nEthernet, no interfaces are up. Is " \
			"the network cable plugged in?" 
		ERR_CODE=323
		 
		log_error $ERR_CODE $FUNC_TYPE " "
		return
	else
		for interface in $test_interfaces ;do
			echo -n -e "$interface," 
			TEST_IFACES+=" $interface"
			tmp=$(ping -W 1 -q -c 1 -I $interface $PING_DESTINATION | \
				awk '$1 == $4 && /packets\ transmitted/ { printf "success" }')
	
			if [ "x$tmp" == "x" ] ;then 
				echo -e "FAIL,\nEthernet, on $interface $PING_DESITNATION unreachable" 
				ERR_CODE=324

				log_error $ERR_CODE $FUNC_TYPE $interface
				return
			fi 

		done
	fi

	echo -e -n "PASS \n" 
	log_error $ERR_CODE $FUNC_TYPE " "
}

function test_wifi() {
	local FUNC_TYPE="010-01"
	local ERR_CODE=0

	DEV=${1:?}
	WPA_CONF=${2:-"/etc/wpa_supplicant/wpa_supplicant.conf"}

	wpa_supplicant -Dwext -i$DEV -c$WPA_CONF

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE " "
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function wifi_device_test() {
		test_wifi $@
	}

# Block device testing functions

function type_block() {
	local DEV=${1}
	
	udevadm info --export-db | grep -E -A 12 "block.*${DEV}" 

	# if anyone can think of a clean, reliable way to determine what type of
	# device is being tested from here, the use of ID_FILE may not be 
	# necessary
}

function check_block() {
	local DEV_SD=$(find /dev/ -regex ".*sd." ! -regex ".*\..*" | awk -F/ \
		'{print $3}')

	for each in $DEV_SD ;do
		echo $each
		type_block $each		
	done
}

function ll_block() {

	local MOUNT=$(mount | grep $1 | awk '{print $3}')
    echo $MOUNT

	if [ ! -b "/dev/${1}" ] ;then
		echo "ERROR: No such block device: /dev/${1}" \
			
		return -3
	fi

	if [ "x$MOUNT" == "x" ] ;then
		MOUNT=/media/$1
		echo "Mounting /dev/$1 on $MOUNT" 
		mkdir -p $MOUNT
		mount -t auto /dev/$1 $MOUNT  2>&1
		
		#TODO need to check the output of mount and produce an error
		# based on that output if necessary
	fi

	# print out the ID string located in a plain text file in the top-level
	# directory of the mount. This file shall be called...ID_FILE and only
	# its first line is to be printed out. this first line should have
	# identifying information...if not, then why bother?
	ID_FILE="$MOUNT/ID_FILE $MOUNT/id_file" 

	for file in $ID_FILE; do
		if [ -f "$file" ] ;then
			local ID=$(head -n 1 $file)
			echo $ID 
			break
		else
			echo "WARNING: No $file in $MOUNT!" 
		fi
	done

	$TEST_BIN block_device_test $MOUNT  
}

function test_block() {
	local FUNC_TYPE="002-01"
	local ERR_CODE=0

	local DEV=${1:?}

	ll_block $DEV

	ERR_CODE=$?

	umount -t /dev/$DEV 

	log_error $ERR_CODE $FUNC_TYPE ${DEV}
}

#TODO: finish building the test_usb_gadget test
function test_usb_gadget() {
	local FUNC_TYPE="015-01"
	local ERR_CODE=0

	local BACKING_FILE=${1-?}
	local DEV=${2-?}
    local MOD=${3-"no"}


	if [ "x$BACKING_FILE" == "x" ] ;then
		echo "usage: usb_gadget_test <BACKING_FILE_name>"

	# can't use fdisk automated, so should just exit gracefully
	#if [ ! -f "$BACKING_FILE" ] ;then
		#dd bs=1M count=2 if=/dev/zero of="$BACKING_FILE"
	#fi

        #exec 1>&30 30>&-

		return -1
	fi

	# load modules

	depmod -a 

    if [ "x$MOD" != "xno" ] ;then
	    for each in usb-storage ohci-hcd ehci-hcd ;do
		    modprobe $each
	    done
    fi

	modprobe g_file_storage file=$BACKING_FILE removable=y

    sleep 5
	# run block_device test
	
	ll_block $DEV
	
	ERR_CODE=$?

	umount -t $MOUNT 

	log_error $ERR_CODE $FUNC_TYPE ${DEV}
}

function config_usb_otg() {
    local TYPE=${1:?}

    local GPIO_PATH=/sys/class/gpio/otgpwren
    local GPIO_DATA=${GPIO_PATH}/data
    local VALS

    if [ -f ${GPIO_DATA} ] ;then
		case ${TYPE} in
		'host')
	        VALS="0 1"
			;;
		'device')
	        VALS="1 0"
			;;
		*)
	        return -1
			;;
		esac

	    for each in ${VALS} ;do
	        echo ${each} > ${GPIO_DATA}
	        sleep 1
	    done
    else
        return 0
	fi
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function block_device_test() {
		test_block $@	
	}

# Video testing functions

function test_vid_ts() {
	local FUNC_TYPE="012-01"
	local ERR_CODE=0
    # why is this empty local declaration here??
	#local
	
	yes_no video

	yes_no touchscreen

	ERR_CODE=$?

	if [ $ERR_CODE -ne 0 ] ;then
		describe
		log_error $ERR_CODE $FUNC_TYPE "$EXTRA_INFO"
		return 0
	fi

	log_error $ERR_CODE $FUNC_TYPE " "
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function vid_ts_test() {
		test_vid_ts
	}
	
# Audio testing functions

function test_audio_out() {
	local FUNC_TYPE="003-01"
	local ERR_CODE=0

	local command=${1:-"wave"}

	amixer set Master 100% > /dev/null
	amixer set Headphone 100% > /dev/null
	amixer set Speaker 100% > /dev/null
	amixer set Line-Out 100% unmute > /dev/null

	case $command in
	'sine')
		;;
	'wave')
		;;
	*)
		command="wave"
		;;
	esac

	speaker-test -c 2 -t $command -l 1 2 -f 1000 
	
	yes_no audio

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE " "
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function audio_out_test() {
		test_audio_out $@
	}

function test_audio_inout() {
	local FUNC_TYPE="004-01"
	local ERR_CODE=0

	echo "audio test initialized" 

	killall arecord aplay > /dev/null 2>&1

	arecord -f dat | aplay > /dev/null 2>&1 &

	if [ "x$1" == "x1" ] ;then
		read
		killall arecord aplay
	fi

	yes_no audio

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE " "
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function audio_inout_test() {
		test_audio_inout $@
	}

# Serial testing functions

function check_serial_loop() {
	for i in 0 4 5 6 7 8 9 10 11 ;do 
		temp=$($TEST_BIN serial_test /dev/ttyS$i | awk '{print $5}')
		if [ "x$temp" = "xOK" ] ;then
			echo "loopback on /dev/ttyS$i"
			return 0
		fi
	done

	return 1
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function which_serial() {
		check_serial_loop $@
	}

function check_serial_enumeration() {
	local tmp
	local i=1

	for each in /dev/ttyS4 /dev/ttyS6 ;do
		$TEST_BIN serial_test /dev/ttyS4 /dev/ttyS5 > /dev/null 2>&1
		tmp=$?
		if [ "x$tmp" == "x0" ] ;then
			return $i
		fi
		i=$((i+1))
	done

	return -2
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function test_serial_enumeration() {
		check_serial_enumeration $@
	}

function test_serial() {
	local FUNC_TYPE="005-01"
	local ERR_CODE=0

	local DEV_ONE=${1:?}
	local DEV_TWO=${2}

	for each in $DEV_ONE $DEV_TWO ;do
		if [ ! -e $each ] ;then
			echo "WARNING: $each does not exist! Test Aborted " \
				"with no log entry."
			return -3
		fi
	done

	if test $ERR_CODE ;then
		$TEST_BIN serial_test $DEV_ONE $DEV_TWO  
	fi

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$DEV_ONE <-> ${DEV_TWO:-${DEV_ONE}}"
}

# deprecated in favor of different naming convention, retained for
# compatibility reasons
	function test_serial_device() {
		test_serial $@
	}

function test_pwm() {
	local FUNC_TYPE="016-01"
	local ERR_CODE=0

	local DEV=${1:?}
	local MSG=${2:-"PWM"}

	local widthus="/sys/class/pwm/$(echo -n $DEV | awk -F\/ \
		'{print $3}')/widthus"

	# TODO: get a C function working here
	echo 0 > ${widthus} && sleep 1 && echo 255 > ${widthus}

	yes_no ${MSG}

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "${MSG}"
}

function test_485() {
	local FUNC_TYPE="009-01"
	local ERR_CODE=0

	local DEV=${1:?}

	$TEST_BIN 485_test $DEV

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$DEV"
}

# analog testing functions

function test_analog() {
	local FUNC_TYPE="007-01"
	local ERR_CODE=0

	local TYPE_DEV=${1:-mcp3208}
	local NUM_DEV=${2:-11}
	local MSG=${3:-"AtoD"} 

	case $TYPE_DEV in
	'mcp3208')
		$TEST_BIN mcp3208_analog_test /dev/mcp3208 $NUM_DEV 1 | \
			$DIALOG --title "Analog Gauge" --gauge "Gauge Widget." \
			10 70 0
		;;
	'mcp3208-plain')
		$TEST_BIN mcp3208_analog_test /dev/mcp3208 $NUM_DEV 1 
		;;
	'gpio')
		$TEST_BIN gpio_analog_test /dev/indexed_atod $NUM_DEV  1 | \
			$DIALOG --title "Analog Gauge" --gauge "Gauge Widget." \
			10 70 0
		;;
	'gpio-plain')
		$TEST_BIN gpio_analog_test /dev/indexed_atod $NUM_DEV  0
		;;
	*)
		;;
	esac


	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$TYPE_DEV: $MSG"

	return 0


	PCT=0
	(
	while test $PCT != 110
	do
		cat <<EOF
XXX
$PCT
New Message.
XXX
EOF
		PCT=$(($PCT + 10))
		sleep 1
	done
	)
}

# gpio testing functions

function test_gpo() {
	local FUNC_TYPE="013-01"
	local ERR_CODE=0

	local DEV=${1:?}
	local VAL=${2:?}
	local MSG=${3:-"GPO"}

	echo "Testing $MSG"

	$TEST_BIN gpo_test $DEV $VAL  

	yes_no "$MSG"

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$DEV: $MSG"
}

function test_gpi() {
	local FUNC_TYPE="014-01"
	local ERR_CODE=0

	local DEV=${1:?}
	local MSG=${2:-"GPI"}

	$TEST_BIN gpi_test $DEV 1 | $DIALOG --title "GPI Gauge" --gauge \
		"Gauge Widget." 10 70 0

	yes_no "$MSG"

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$DEV: $MSG"

}

function test_rtc() {
	local FUNC_TYPE="011-01"
	local ERR_CODE=0

	local DEV=${1:?}

	$TEST_BIN rtc_test $DEV 

	ERR_CODE=$?

	log_error $ERR_CODE $FUNC_TYPE "$DEV"
}

