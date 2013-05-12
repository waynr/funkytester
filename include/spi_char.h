#ifndef SPI_CHAR_H_
#define SPI_CHAR_H_

#include <asm/types.h>
#include <sys/types.h>

/**
 * Userspace version of kernel header
 */

#define SPICL_CPHA          (0x01)
#define SPICL_CPOL          (0x02)

/* common bit settings -- should be mutually exclusive */

#define SPICL_EIGHTBIT      (0x04) /* 8 bit is default */
#define SPICL_TENBIT        (0x08) /* 10 bits per transfer */ 
#define SPICL_TWELVEBIT     (0x10) /* 12 bits per transfer */
#define SPICL_SIXTEENBIT    (0x20) /* 16 bits per transfer */

typedef __u8 spi_data;
typedef __u32 spi_control;

typedef struct spi_transfer_s {
    spi_data *mosi;
    spi_data *miso;
    ssize_t size;
} spi_transfer_t;

#include <linux/ioctl.h>

//arbitrary assignment, come back to this later
#define CHAR_CLASS_SPI 0x90 

#define CONFREAD        _IOR(CHAR_CLASS_SPI,0,spi_control)
#define CONFWRITE       _IOW(CHAR_CLASS_SPI,0,spi_control)
#define SPEEDREAD       _IOR(CHAR_CLASS_SPI,1,spi_control)
#define SPEEDWRITE      _IOW(CHAR_CLASS_SPI,1,spi_control)
#define TIPREAD         _IOR(CHAR_CLASS_SPI,2,spi_control)
#define TIPWRITE        _IOW(CHAR_CLASS_SPI,2,spi_control)
#define XMIT            _IOW(CHAR_CLASS_SPI,3,spi_transfer_t)

#endif /*SPI_CHAR_H_*/
