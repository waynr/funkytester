#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <stdio.h>

#include <asm/types.h>
#include "spi_char.h"

/**
 * function to setup the temperature ADC
 * @return open file descriptor on success -1 on error
 */
int init_spi(char *dev)
{
    int fd;
    static spi_control config = SPICL_EIGHTBIT;
    
    if ((fd = open(dev, O_RDWR)) == -1) {
        return -1;
    }
    /* confwrite to set bpw to 8 , mode 0,0 (CPHA and CPOL 0) */
    if ((ioctl(fd, CONFWRITE, &config)) == -1) {
        return -1;
    }
    return fd;
}

/**
 * function to read the temperature ADC at a specific index
 * @param reg the index to read from
 * @param fd the file descriptor for the open device
 * @return the value read from the ADC
 */
__u16 mcp3208_read_index(__u8 reg, int fd)
{
    spi_transfer_t data;
    __u8 reg_msb;
    __u8 mosi[3];
    __u8 miso[3];
    __u16 ret;
    
    /*
     * The command for the mcp3208 is as follows:
     * leading 0's
     * start bit
     * 1 to signal single mode
     * 3 bits to represent the channel to read
     */
    data.size = 3; /* 24 bits */
    
    reg_msb = (reg >> 2) & 0x01; /* XYZ >> 2 = X */
    mosi[0] = reg_msb | 0x06;
    /* the last 2 bits of the reg need to go into the top of the
     * second byte transmitted */
    mosi[1] = reg << 6; /* 00000xxx << 6 = xx000000 */
    
    memset(miso, 0x0, sizeof(miso));
    
    data.mosi = mosi;
    data.miso = miso;
    
    if (ioctl(fd, XMIT, &data) == -1) {
        fprintf(stderr, "Error reading from SPI\n");
        return 0;
    }
    ret = ((miso[1] & 0x0F) << 8) | (miso[2] & 0x00FF);
    return ret;
}
