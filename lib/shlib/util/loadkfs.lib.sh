#!/bin/bash


function flash_format() {
    local DEVICE=${1:-?}
    local MSDOS_SIZE=${2:-?}

    fdisk -H 255 -S 63 ${DEVICE} << EOF
n
p
1

+${MSDOS_SIZE}
n
p
2


t
1
c
a
1
w
EOF
}

function program_mmc() {
    local MSDOS_DEV=${1:-?}
    local EXT3_DEV=${2:-?}
    local IMAGES_DIR=${3:-?}
    local MSDOS_SIZE=${4:-?}

    local MOUNT_POINT=/mnt/card

    sleep 1

    # U-Boot partition
    mkdosfs -F 32 ${MSDOS_DEV}
    mount ${MSDOS_DEV} ${MOUNT_POINT}

    pushd ${IMAGES_DIR}
    cp MLO uImage u-boot.bin ${MOUNT_POINT}

    sync
    umount ${MSDOS_DEV}

    # Linux rootfs
    mkfs.ext3 ${EXT3_DEV}
    mount ${EXT3_DEV} ${MOUNT_POINT}

    pushd ${MOUNT_POINT}
    tar xzf ${IMAGES_DIR}/fs.tar.gz
    rm etc/ssh/ssh_host_*
    popd

    popd

    sync
    umount ${EXT3_DEV} 
}
