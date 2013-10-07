#!/bin/bash

INTERFACE=${1:?}
ESSID=${2:?}

#-------------------------------------------------------------------------------
# Functions
#

pass() {
	echo "PASS"
	echo "WiFi Signal quality > 70/100"
	exit 0
}

fail() {
	local q=${1:?}
	echo "FAIL"
	echo "${q}"
	exit 1
}

#-------------------------------------------------------------------------------
# Main
#
( ip addr | grep ${INTERFACE} 2>&1 > /dev/null ) || \
	fail "WiFi interface (${INTERFACE}) appears to be missing." 

quality=` iwlist "${INTERFACE}" scan \
	| grep -A 3 ${ESSID} \
	| awk 'BEGIN { FS="[=\ /:]+" } /Quality/ { print $3 }' `

( [ "${?}" != "0" ] || [ "${quality}" == "" ] ) && \
	fail "WiFi access point (${ESSID}) appears to be missing."

[ "${quality}" -lt "70" ] && \
	fail "WiFi Signal quality (${quality}) must be > 70/100 to pass."

pass

