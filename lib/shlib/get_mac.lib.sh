#!/bin/bash

function get_serial() 
{
	if [ "x$SERIALNUM" == "x" ] ;then
		read -n 11 -p "Enter the UUT's Serial#: " SERIALNUM
	fi
}

function request_mac()
{
	ACHIEVO="http://localhost/achievo"
	ACHIEVO="http://10.0.2.85/achievo/"
	ACHIEVO="http://internal.emacinc.com/achievo/"

	ACHIEVO_USER="achievo"
	ACHIEVO_PW="XNm2J2AntD2WhmZ8"
	ACHIEVO_USER="achievo-user"
	ACHIEVO_PW="UGaE1eds0cjgBwm4"
	ACHIEVO_USER="TESTSET"
	ACHIEVO_PW="som200"

	COOKIES="/tmp/cookies.txt"

	MACPERMOD="${1:-1}"

	IHWO_REF=${2:-$IHWO_REF}

	get_serial

	# CMD_WGET="wget -v --no-check-certificate --keep-session-cookies "
	# CMD_WGET="wget -v --keep-session-cookies "
	CMD_WGET="wget" # --keep-session-cookies "
	
	rm -f "/tmp/mac.html" 2>/dev/null
	
	# login
	$CMD_WGET \
		--save-cookies $COOKIES \
		--output-document="/tmp/login.html" \
		--post-data="auth_user=$ACHIEVO_USER&auth_pw=$ACHIEVO_PW&form_id=loginform" "$ACHIEVO"
	
	# wget what we came for
	$CMD_WGET \
		--save-cookies $COOKIES \
		--load-cookies $COOKIES \
		--output-document="/tmp/mac.html" \
		--post-data="atknodetype=inventory.inventory_macaddr&atkaction=dispense&uid=5&ssn=$SERIALNUM&qty=$MACPERMOD&ref=$IHWO_REF&port=0" "$ACHIEVO/dispense.php"

	# logout
	$CMD_WGET \
		--save-cookies $COOKIES \
		--load-cookies $COOKIES \
		--output-document="/tmp/logout.html" \
		--post-data=atklogout=1  "$ACHIEVO"

}
