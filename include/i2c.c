#include <stdio.h>
#include <termios.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>

#include "i2c-dev.h"

/**
 * function to set the slave address of the i2c device. This only needs to be
 * done to initialize the address and then each time that a new device is
 * addressed. 
 * @note this is the lower 7 bits of the devices slave address
 * @param fd the file descriptor of the open i2c device
 * @param addr the slave address to set
 * @return -1 on error 0 on success
 */
inline int i2c_set_slave(int fd, int addr)
{
	if (ioctl(fd, I2C_SLAVE, addr) < 0) {
		fprintf(stderr, "i2c_set_addr: Error on ioctl: %s\n",
				strerror(errno));
		return -1;
	}
	return 0;
}

/**
 * function to write one byte to the i2c device. 
 * @param fd the open file descriptor of the i2c device
 * @param data the byte to write to the device
 * @return -1 on failure 0 on success
 */
inline int i2c_write_byte(int fd, __u8 byte)
{
	i2c_smbus_write_byte(fd, byte);
	return 0;
}

/**
 * function to write a byte to a specific register in the device. 
 * @param fd the open file descriptor for the i2c device
 * @param reg the register to write to
 * @param cmd the data to write to the device
 * @return -1 on failure 0 on success
 */
inline int i2c_write_cmd(int fd, __u8 reg, __u8 cmd)
{
	__u8 buff[2];

	buff[0] = reg;
	buff[1] = cmd;
	
	i2c_smbus_write_byte_data(fd, reg, cmd);
	return 0;
}

/**
 * function to read a byte from the i2c device. 
 * @param fd the open file descriptor for the i2c device
 * @param val a pointer to the location to store the data
 * @return -1 on failure 0 on success
 */
inline int i2c_read_byte(int fd, __u8 *val)
{
	*val = i2c_smbus_read_byte(fd);
	return 0;
}

/**
 * function to read the value at a given register in the i2c device.
 * Currently works by writing the register followed by reading the next byte.
 * @param fd the file descriptor of the open i2c device
 * @param val the memory to store data in
 * @param reg the register to read from
 * @return -1 on failure 0 on success
 */
inline int i2c_read_reg(int fd, __u8 *val, __u8 reg)
{
	/* write register */

	*val = i2c_smbus_read_byte_data(fd, reg);
	return 0;
}
