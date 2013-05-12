#ifndef SPI_H_
#define SPI_H_

int init_spi(char *);
__u16 spi_read_index(__u8 reg, int fd);

#endif /*SPI_H_*/
