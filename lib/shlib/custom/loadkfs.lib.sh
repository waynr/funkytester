#!/bin/bash

. lib/util/loadkfs.lib.sh


function loadkfs() {
    # Suggested calling format (customize if necessary but try to stay general.
    # see the standard "program_mmc" for an example)
    #local MSDOS_DEV=${1:-?}
    #local EXT3_DEV=${2:-?}
    #local IMAGES_DIR=${3:-?}
    #local MSDOS_SIZE=${4:-?}

    # Default actions, feel free to modify

    flash_format ${FLASH_FORMAT_args}
    program_mmc ${PROGRAM_MMC_args}
}
