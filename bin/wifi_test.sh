#!/bin/bash

INTERFACE=${1:?}

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
quality=` iwlist "${INTERFACE}" scan \
	| grep -A 3 evsc \
	| awk 'BEGIN { FS="[=\ /]+" } /Quality/ { print $3 }' `

( [ "${?}" != "0" ] || [ "${quality}" == "" ] ) && \
	fail "WiFi interface (${1}) appears to be missing."

[ "${quality}" -lt "70" ]  && \
	fail "WiFi Signal quality (${quality}) must be > 70/100 to pass."

pass

