#!/bin/bash

. lib/get_mac.lib.sh
. lib/util/output.lib.sh

# pull in code from the loadkfs library which  should provide the "loadkfs"
# function to be used in this menu.
. lib/custom/loadkfs.lib.sh

function advanced_options_menu() {	
    # assumes that the script which sources this this script has also source
    # ./lib/emac_test_functions.lib.sh
	
	. ./lib/menu/dialog.libcfg.sh

	. ./lib/menu/main_menu.libcfg.sh

    local tmp_OUTPUT_FILE=advanced_options_output
	
	until [ $STATUS == 255 ] ;do
		
		$DIALOG --title "EMAC Carrior Board Test Results" \
		--begin $RESULTS_STARTY $RESULTS_STARTX \
		--tailboxbg $tmp_OUTPUT_FILE $RESULTS_ROWS $RESULTS_WIDTH \
		--and-widget \
		--title "EMAC Carrier Board Test Set" \
		--cancel-label "Quit" \
		--begin $MENU_STARTY $MENU_STARTX \
		--menu \
		"Select the function you wish to run:" $MENU_ROWS $MENU_WIDTH 8 \
        "Memtester"	"Test the device system memory. (takes a while)" \
        "loadkfs"	"Load U-Boot, kernel, and filesystem onto eMMC." \
		"Reset"		"Reset the test results" 2> $tempfile
		
		retval=$?
	
		choice=$(cat $tempfile)
		
        redirect save

        STATUS=0
	    
		case $retval in
		0)
			case $choice in
			'Memtester')
				test_mem >> $tmp_OUTPUT_FILE
            ;;
			'loadkfs')
				loadkfs
			;;
			'Reset')
				echo "" > $tmp_OUTPUT_FILE
			;;
			*)
                # default STATUS if no menu selection was made. This fixes the
                # odd case where selecting "Quit" (see man dialog DIAGNOSTICS
                # section) does not produce a return value of 1. 
                STATUS=255
			;;
			esac

            if [ ! "x${choice}" == "xReset" ] ;then
			    echo "== == == == == ==" >> $tmp_OUTPUT_FILE
            fi
		
            redirect restore
			;;
		1)
			echo "Cancel pressed." >> $tmp_OUTPUT_FILE
			rm -rf $tempfile
			STATUS=1
			break
			;;
		255)
			echo "ESQ pressed."
			STATUS=255
			;;
		esac
	done

    redirect save
	
}

function select_ref() {
    redirect restore

	DIALOG=$(which dialog)

	exec 3>&1
	choice=$($DIALOG --nocancel \
	--title "EMAC Carrier Board Test Set" \
	--default-item "IHWO#1309-9G20" "$@" \
	--clear \
	--menu "Select the Reference Number:" 10 51 4 \
	"IHWO#1309-9G20"		"" \
	"IHWO#31182-9G20"		"" \
	"IHWO#31363-SOM9G45"		"" \
	"IHWO#1260-9307.6-11.RVSN2"	"" \
	2>&1 1>&3)
	
	retval=$?

	exec 3>&-


	case $retval in
	0)
		case $choice in
		'IHWO#1309-9G20')
			IHWO_REF="IHWO%231182-9G20"
		;;
		'IHWO#1182-9G20')
			IHWO_REF="IHWO%231309-9G20"
		;;
		'IHWO#1363-SOM9G45')
			IHWO_REF="IHWO%231363-SOM9G45"
		;;
		'IHWO#1260-9307.6-11.RVSN2')	
			IHWO_REF="IHWO%231260-9307.6-11.RVSN2"
			export IHWO_REF
		;;
		*)
		;;
		esac

		;;
	1)
		echo "Cancel pressed."
		rm -rf $tempfile
		;;
	255)
		echo "ESQ pressed."
		;;
	esac
    redirect save
}

function input_serial() {
    redirect restore
	DIALOG=$(which dialog)

	exec 3>&1
	SERIALNUM=$($DIALOG --nocancel \
		--title "Serial Number Entry" --clear \
		--inputbox "Please enter the UUT Serial Number" 8 51 \
	2>&1 1>&3)
	
	retval=$?

	exec 3>&-

	case $retval in
	0)

		request_mac

		MAC=$(awk '{print $2}' /tmp/mac.html)

		;;
	1)
		echo "Cancel pressed."
		rm -rf $tempfile
		;;
	255)
		echo "ESQ pressed."
		;;
	esac
    redirect save
}

function yes_no() {
    redirect restore
	TEST_TYPE_NAME=${1:-""}
	$DIALOG --title "Pass/Fail" --yes-label "Pass" --no-label "Fail" --clear \
		--yesno "Please indicate whether the ${TEST_TYPE_NAME} test passed or \
failed." 0 0 
    redirect save
}

function describe() {
    redirect restore
	local tempfile="/tmp/describe$$"
	trap "rm -r $tempfile" 0 1 2 5 15
	
	$DIALOG --title "Failure Notes" --clear \
		--inputbox "Please enter a description of the observed \
failure. Include as much specific information as possible." 11 51 2> \
$tempfile
	
	#NOTE: EXTRA_INFO is local to the calling function and is intended to be
	# used by log_error
	EXTRA_INFO=$(cat $tempfile)
    redirect save
}
