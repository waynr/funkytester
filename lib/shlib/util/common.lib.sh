#!/bin/bash

function util_source_resize() {
	RESIZE_TMP="/tmp/resize-$RANDOM"

	RESIZE="$(which busybox) resize"
    #RESIZE="resize"

	$RESIZE

	if [ "x$?" == "x1" ] ;then
		RESIZE=$(which resize)
	fi

	$RESIZE > $RESIZE_TMP
	
	. $RESIZE_TMP 
	
	rm -f $RESIZE_TMP
}


function source_ifexists() {
    local FILE=${1:-?}
    local EXITIFNOT=${2:-1}

    if [ -f ${FILE} ] ;then
        source ${FILE}
    fi

    echo "${FILE} not found."

    if [ ${EXITIFNOT} -eq 1 ] ;then
        exit -1
    fi
}
