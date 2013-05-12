#!/bin/sh


function redirect() {
    local CMD=${1:?}

    case ${CMD} in
    save)
	    if [ "x${OUT}" != "xstdout" ] ;then
		    exec 30>&1
		    exec 29>&2
	        exec >> ${OUTPUT_FILE} 2> ${OUTPUT_FILE}.log
	    fi
        ;;
    restore)
	    if [ "x${OUT}" != "xstdout" ] ;then
	        exec 1>&30 30>&- 2>&29 29>&-
	    fi
        ;;
    *)
        echo "Bad command."
        exit 1
        ;;
    esac
}
