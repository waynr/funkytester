/*
 * Copyright 2011 EMAC Inc
 *
 * Test library that should simplify the creation of new software testsets for
 * EMAC producets. 
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <ctype.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <asm/types.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <time.h>
#include <linux/rtc.h>
#include <termios.h>

#include "rs485.h"
#include "gpio.h"
#include "serial.h"
#include "ping.h"
#include "kbhit.h"
#include "i2c.h"
#include "i2c-dev.h"
#include "spi.h"

#include "emac_generic_tests.h"
#include "emac_errors.h"

// TODO, properly include pwm.h
#include "pwm_dm.h"

int test_block(char * mnt_pt)
{
	struct statfs statbuf;
	struct statfs rootfs_statbuf;
	int free;
	int timeout;
	int good = 0;
	char buff[8192]; /* 2 pages */
	char r_buff[8192];
	char test_file[256];
	FILE *stream;

	memset(buff, 0xAA, sizeof(buff));

	printf("Block Device Test(%s):\t\t\t",mnt_pt); 
	fflush(stdout);

	sprintf(test_file, "%s/test", mnt_pt);

	for (timeout = 2; (timeout && !good); timeout--) {
		if (statfs("/etc", &rootfs_statbuf) == -1) {
			printf("FAIL: block device test unable to open file: %s\n", strerror(errno));
			break;
			sleep(1);
			continue;
		}
		if (statfs(mnt_pt, &statbuf) == -1) {
			printf("FAIL: block device test unable to open file: %s\n", strerror(errno));
			break;
			sleep(1);
			continue;
		}

		if(statbuf.f_blocks * statbuf.f_bavail == rootfs_statbuf.f_blocks * rootfs_statbuf.f_bavail) {
			printf("FAIL: block device not mounted at %s\n",mnt_pt);
			return BLOCK_NO_MOUNT;
		}

		if ((statbuf.f_type == JFFS2_TYPE) || 
				(statbuf.f_type == TMPFS_TYPE) || 
				(statbuf.f_type == NFS_TYPE)) {
			/* stat is really on root flash, RAM, or NFS -- not USB */
			sleep(1);
			continue;
		}
		/* convert the number from blocks to kilobytes */
		free = (statbuf.f_bavail*statbuf.f_bsize+512)/(1024*1024);

		/* write / read test */
		if (!(stream = fopen(test_file, "w+"))) {
			printf("FAIL: block device test unable to open file: %s\n", strerror(errno));
			return FD_NO_OPEN;
		}
		if ((fwrite(buff, 1, sizeof(buff), stream) != sizeof(buff))) {
			printf("FAIL: block device test unable to write: %s\n", strerror(errno));
			fclose(stream);
			unlink(test_file);
			return FD_NO_WRITE;
		}
		/* flush data */
		fflush(stream);
		sync();
		/* go to beginning of file */
		rewind(stream);
		if ((fread(r_buff, 1, sizeof(r_buff), stream) != sizeof(buff))) {
			printf("FAIL: USB test unable to read data: %s\n", strerror(errno));
			fclose(stream);
			unlink(test_file);
			return FD_NO_READ;
		}
		fclose(stream);
		unlink(test_file);
		if ((memcmp(buff, r_buff, sizeof(buff))) != 0) {
			printf("FAIL: USB test found read/write data mismatch\n");
			return BUF_CMP_FAIL;
		}
		good = 1;
	}

	if (!timeout) {
		printf("FAIL: timeout\n");
		return TIMEOUT;
	}

	printf("PASS\n");
	fflush(stdout);
	return SUCCESS;
}

/**
 * port1 rx should be connected to port2 tx
 * port2 rx should be connected to port1 tx
 */
int test_serial(char *port1, char *port2) 
{
	const char *buff = "hello serial port how are you??";
	char r_buff[strlen(buff)+1];

	int fd1;
	int fd2 = 0;
	int *fd_pointer = &fd1;
	int numread;


	fprintf(stdout,"Serial Device Test %s  %s:\t\t", port1 , port2);
	fflush(stdout);
		
	if (strcmp(port1, port2) != 0) {
		if ((fd2 = open(port2, O_RDWR | O_NONBLOCK)) == -1) {
			printf("FAIL (open: %s)\n", strerror(errno));
			errno = 0;
			return FD_NO_OPEN;
		}
		fd_pointer = &fd2;
		setup_serial(fd2, B115200, 0);
	}
	
	if ((fd1 = open(port1, O_RDWR | O_NONBLOCK)) == -1) {
		printf("FAIL (open: %s)\n", strerror(errno));
		errno = 0;
		return FD_NO_OPEN;
	}

	setup_serial(fd1, B115200, 0);

	if (write(fd1, buff, strlen(buff)+1) != strlen(buff)+1) {
		printf("FAIL (write: %s)\n", strerror(errno));
		errno = 0;
		close_fd(fd1, fd2);
		return SERIAL_WRITE;
	}
	if (poll_serial(*fd_pointer) != 1) {
		printf("FAIL (poll)\n"); 
		fflush(stdout);
		close_fd(fd1, fd2);
		errno = 0;
		return SERIAL_POLL;
	}

	usleep(50000);

	if ((numread = read(*fd_pointer, r_buff, strlen(buff)+1)) != strlen(buff)+1) {
		printf("FAIL (read: %d: %s)\n", numread, strerror(errno));
		errno = 0;
		close_fd(fd1, fd2);
		return SERIAL_READ;
	}
	if (memcmp(buff, r_buff, strlen(buff)+1) != 0) {
		printf("FAIL (compare failed)\n"); 
		fflush(stdout);
		close_fd(fd1, fd2);
		return BUF_CMP_FAIL;
	}

	if (*fd_pointer != fd1) {
		if (write(*fd_pointer, buff, strlen(buff)+1) != strlen(buff)+1) {
			printf("FAIL (write: %s)\n", strerror(errno));
			errno = 0;
			close_fd(fd1, fd2);
			return SERIAL_WRITE;
		}
		if (poll_serial(fd1) != 1) {
			printf("FAIL (poll)\n"); 
			fflush(stdout);
			close_fd(fd1, fd2);
			errno = 0;
			return SERIAL_POLL;
		}
			usleep(50000);
		if ((numread = read(fd1, r_buff, strlen(buff)+1)) != strlen(buff)+1) {
			printf("FAIL (read: %d: %s)\n", numread, strerror(errno));
			errno = 0;
			close_fd(fd1, fd2);
			return SERIAL_READ;
		}
		if (memcmp(buff, r_buff, strlen(buff)+1) != 0) {
			printf("FAIL (compare failed)\n"); 
			fflush(stdout);
			close_fd(fd1, fd2);
			return BUF_CMP_FAIL;
		}
	}

	printf("PASS\n"); 
	fflush(stdout);

	close_fd(fd1, fd2);

	return SUCCESS;
}

int test_pwm(char *pwm_dev)
{
	char *device;
	int pwm;
	char pwm_c;

	if (pwm_dev  == NULL) 
		device = PWM_DEFAULT;
	else
		device = pwm_dev;

	printf("Testing the PWM:\t\t\t\t\t"); 
	fflush(stdout);

	if ((pwm = open(device, O_WRONLY)) == -1) {
		printf("FAIL\n Error opening pwm: %s\n", strerror(errno));
		fflush(stdout);
		return FD_NO_OPEN;
	}

	if (ioctl(pwm, WIDTHUSWRITE, &pwm_c) == -1) { 
		printf("FAIL\n Error writing pwm: %s\n", strerror(errno));
		fflush(stdout);
		close(pwm);
		return PWM_NO_WWRITE;
	}

	printf("PASS\n");
	fflush(stdout);

	return SUCCESS;
}

/* if one of the directories exists, the PLD key was detected */
int test_pld(char *gpio_dir)
{
	struct stat s;
	char *directory;

	if (gpio_dir == NULL) 
		directory = PLD_DIR;
	else
		directory = gpio_dir;

	printf("Checking for PLD detection:\t\t\t"); 
	fflush(stdout);

	if (stat(directory, &s) == -1) {
		printf("FAIL\n"); 
		fflush(stdout);
		
		return PLD_DIR_MIS; 
	}

	if (S_ISDIR(s.st_mode)) {
		printf("PASS\n");
	}
	else {
		printf("FAIL\n");
		return PLD_NOT_DIR;
	}

	fflush(stdout);

	return SUCCESS;
}

int test_gpio(char *gpio_port, char *gpio_pattern)
{
	int fd;
	int pattern;
	char *device;
	__u32 value;

	if (gpio_port == NULL) 
		device = GPIO_PORT;
	else
		device = gpio_port;

	if (gpio_pattern == NULL) 
		pattern = GPIO_PAT;
	else
		pattern = strtol(gpio_pattern, NULL, 0);

	printf("Testing GPIO: /t/t/t/t");
	fflush(stdout);

	if ((fd = gpio_dev_open(device)) == -1) {
		printf("FAIL\n Failed to open device, %s: %s\n", device,
				strerror(errno));
		return FD_NO_OPEN;
	}

	if ((value = gpio_read(fd)) == -1) {
		printf("FAIL\n Failed to read device, %s\n", device);
		close(fd);
		return FD_NO_READ;
	}

	if(value != 0xAA) {
		printf("FAIL\n GPIO device value = %.2X ", value);
		close(fd);
		return GPIO_BAD_VAL;
	}
	else {
		printf("PASS\n"); 
		fflush(stdout);
	}

	close(fd);
	return SUCCESS;
}

/* carefully check comm with the RTC without losing the current time */
int test_rtc(char *rtc_dev)
{
	struct timeval tv, tv_c;
	struct tm tm, tm_c;
	int rtc;
	char *device;

	tv.tv_sec = 936868149; /* 09/09/1999 09:09:09 */
	tv.tv_usec = 0;

	if (rtc_dev  == NULL) 
		device = RTC_DEFAULT;
	else
		device = rtc_dev;

	printf("Testing communication with the RTC:\t\t\t"); 
	fflush(stdout);

	/* get the current system time */

	if (gettimeofday(&tv_c, NULL) == -1) {
		printf("FAIL\n Error getting time: %s\n", strerror(errno));
		return RTC_NO_SET;
	}

	/* hose the system time with a bogus value */

	if (settimeofday(&tv, NULL) == -1) {
		printf("FAIL\n Error setting time: %s\n", strerror(errno));
		return RTC_TOD;
	}
	
	if ((rtc = open(device, O_WRONLY)) == -1) {
		printf("FAIL\n Error opening rtc: %s\n", strerror(errno));
		return FD_NO_OPEN;
	}

	/* get the current rtc time */

	tm_c = *(localtime((time_t *)(&tv_c.tv_sec)));
	tm_c.tm_isdst = 0;

	if (ioctl(rtc, RTC_RD_TIME, &tm_c) == -1) {
		printf("FAIL\n Error getting rtc: %s\n", strerror(errno));
		close(rtc);
		return RTC_NO_GET;
	}

	/* hose the rtc with a bogus time */

	tm = *(localtime((time_t *)(&tv.tv_sec)));
	tm.tm_isdst = 0;

	if (ioctl(rtc, RTC_SET_TIME, &tm) == -1) {
		printf("FAIL\n Error setting rtc: %s\n", strerror(errno));
		close(rtc);
		return RTC_NO_SET;
	}

	/* fix the broken rtc time and the system time using values previously
	 * acquired */

	if (settimeofday(&tv_c, NULL) == -1) {
		printf("FAIL\n Error setting time: %s\n", strerror(errno));
		return RTC_TOD;
	}
	
	if (ioctl(rtc, RTC_SET_TIME, &tm_c) == -1) {
		printf("FAIL\n Error setting rtc: %s\n", strerror(errno));
		close(rtc);
		return RTC_NO_SET;
	}

	/* we good */

	printf("PASS\n"); 
	fflush(stdout);

	close(rtc);

	return 0;
}

int test_485(char *dev)
{
	int fd;
	int num;
	char buff[1024];
	char *device;

	memset(buff, 0x0F, BUFF_485);

	if (dev == NULL) 
		device = PORT_485;
	else
		device = dev;

	if ((fd = init_485(device)) == -1) {
		printf("FAIL\n RS-485 test failed on initialization\n");
		return RS485_INIT;
	}
	//printf("A Red LED on the 485 port indicates success\n");
	if ((num = write(fd, buff, BUFF_485)) != BUFF_485) {
		printf("FAIL\n RS-485 test failed to write to port: "
			"%s: %d\n", strerror(errno), num);
		return FD_NO_WRITE;
	}

	close(fd);

	return SUCCESS;
}

/*
 * gpio_dev -	absolute path to the file representing the gpio device.
 * gpio_num -	the number of gpio lines to be read
 * dialog   -	if dialog == 1, then the output is intended to be read by a
 *	gauge dialog widget
 *		else, the output is intended to be viewed on the console's
 *	stdout
 */
int test_analog_gpio(char *gpio_dev, char *gpio_num, char *dialog)
{
	__u8 index;
	int gpio_fd;
	int num_gpio;
	int count = 0;
	char *device;
	char c;

	if (gpio_dev == NULL) 
		device = GPIO_DEV;
	else
		device = gpio_dev;

	if (gpio_num == NULL) 
		num_gpio = NUM_GPIO;
	else
		num_gpio = strtol(gpio_num, NULL, 0);

	if ((gpio_fd = gpio_dev_open(device)) == -1) {
		printf("FAIL\nAnalog test failed opening internal "
			"AtoD device: %s\n", strerror(errno));
		return FD_NO_OPEN;
	}

	if (*dialog == '0') {
		printf("Turn Pots and monitor corresponding channel's "
				"output\npress any key to return to "
				"the menu\n\n");

		for (index = 0; index < num_gpio; index++) {
			printf("V[%d]  ", index);
		}
	
	} 


	printf("\n");

	while (!kbhit()) {
		if (*dialog == '1') {
			printf("XXX\n%d", count);
			count = (count == 100 ) ? 0 : count + 1;
			printf("Turn Pots and monitor corresponding channel's "
					"output\npress any key to return to "
					"the menu\n\n");
			for (index = 0; index < num_gpio; index++) {
				printf("V[%d]  ", index);
			}
		} 

		/* get gpio readings */
		for (index = 0; index < num_gpio; index++) {
			printf("%4d  ", gpio_read_index(index, gpio_fd));
		} 
		if (*dialog == '1') {
			printf("\nXXX");
		} else {
			printf("\r");
		}

		fflush(stdout);
		usleep(SLEEP_US);
	}

	c = getchar();
	close(gpio_fd);
	return SUCCESS;
}

/*
 * spi_dev -	bsolute path to the file representing the gpio device.
 * spi_num -	the number of gpio lines to be read
 * dialog   -	if dialog == 1, then the output is intended to be read by a
 *  gauge dialog widget
 *		else, the output is intended to be viewed on the console's
 *  stdout
 */
int test_analog_mcp3208(char *spi_dev, char *spi_num, char *dialog)
{
	__u8 index;
	int spi_fd;
	int num_spi;
	int count = 0;
	char *device;
	char c;

	if (spi_dev == NULL) 
		device = SPI_DEV;
	else
		device = spi_dev;

	if (spi_num == NULL) 
		num_spi = NUM_SPI;
	else
		num_spi = strtol(spi_num, NULL, 0);

	if ((spi_fd = init_spi(device)) == -1) {
		printf("FAIL\nAnalog test failed opening SPI device: "
			"%s\n", strerror(errno));
		return FD_NO_OPEN;
	}

	if (*dialog == '0') {
		printf("Turn Pots and monitor corresponding channel's "
				"output\npress any key to return to "
				"the menu\n\n");
	} 

	while (!kbhit()) {
		if (*dialog == '1') {
			printf("XXX\n%d", count);
			count = (count == 100 ) ? 0 : count + 1;
			printf("Turn Pots and monitor corresponding channel's "
					"output\npress any key to return to "
					"the menu\n\n");
		} 

		for (index = 0; index < num_spi; index++) {
			printf("P[%d]  ", index);
		}

		printf("\n");

		/* get spi readings */
		for (index = 0; index < num_spi; index++) {
			printf("%4d  ", gpio_read_index(index, spi_fd));
		}

		if (*dialog == '1') {
			printf("\nXXX");
		} else {
			printf("\r");
		}

		fflush(stdout);
		usleep(SLEEP_US);
	}

	printf("\n");
	c = getchar();
	close(spi_fd);

	return SUCCESS;
}

/*
 * device - /dev/ file which, through the linux gpio driver, operates specific
 *  hardware lines on the board being tested. this file abstracts away issues of
 *  addressing the device underconsideration and gives us the ability to write
 *  "on" and "off" values directly using ioctl
 * num_bits - the bit width of the particular device being tested. this will
 *  determine the "size" of the loop through with a single "on" bit will be
 *  sequentially looped from the LSB to the MSB.
 * 
 * generally speaking, it is necessary to give the test operator enough time to
 *  that this test works properly. to that end, it should loop until a key is
 *  hit at which point it will return. It is expected that the calling shell
 *  script will query the test operator to determine pass/fail status.
 */
int test_gpo(char *device, char *num_bits)
{
	int fd;
	int bits = strtol(num_bits, NULL, 0);
	int value = 1;
	char c;

	printf("Checking GPO functionality of %s:\t\t", device); 
	fflush(stdout);

	if ((fd = open(device, O_RDWR)) == -1) {
		printf("FAIL\nGPO test failed opening %s: %s\n", \
				device, strerror(errno));
		return FD_NO_OPEN;
	}

	while (!kbhit()) {
		if (gpio_write(value, fd) == -1) {
			printf("FAIL\nGPO write failed on %s: %s\n", \
					device, strerror(errno));
			return GPIO_NO_WRITE;
		}

		if (value == (1 << bits ))
			value = 1;
		else
			value <<= 1;

		usleep(200000);
	}
	
	c = getchar();

	printf("CHECK\n");
	fflush(stdout);

	close(fd);
	return SUCCESS;
}

int test_gpi(char *device, char *dialog)
{
	int fd;
	int val;
	int count = 0;

	printf("Checking GPI functionality of %s:\t\t", device); 
	fflush(stdout);

	if ((fd = open(device, O_RDWR)) == -1) {
		printf("FAIL\nGPI test failed opening %s: %s\n", \
				device, strerror(errno));
		return FD_NO_OPEN;
	}

	if ((val = gpio_read(fd)) == -1) {
		printf("FAIL\nGPI read failed on %s: %s\n", \
				device, strerror(errno));
		return GPIO_NO_READ;
	}

	if (*dialog == '0') {
		printf("press any key to return to the menu\n\n");
	} 

	while (!kbhit()) {
		if (*dialog == '1') {
			printf("XXX\n%d", count);
			count = (count == 100 ) ? 0 : count + 1;
			printf("press any key to return to the menu\n\n");
		} 

		printf("%4d  ", gpio_read(fd));

		if (*dialog == '1') {
			printf("\nXXX");
		} else {
			printf("\r");
		}

		fflush(stdout);
		usleep(SLEEP_US);
	}

	close(fd);
	return SUCCESS;
}

/*
 * device - /dev/ file which, through the linux I2C driver, works on the I2C
 *  bus to read and write values to the addressed device.
 * i2c_addr - address of the device to be tested on the I2C bus.
 * reg_read - register to be read from the addressed device.
 * expected_value - expected value of the given register at the given I2C
 *  addres.
 *
 * Generally speaking, this test is designed to verify the behavior of the I2C
 * bus on the UUT by reading values from registers whose values are typically
 * well-known, such as version registers. It is important to note that this does
 * not necessarily verify the correct functioning of the I2C device itself.
 *
 */
int test_i2c_read(char *device, char *i2c_addr, char *i2c_reg, char* expected_value)
{
	int fd, num_bytes, expected, actual, reg, addr;
	__u8 b;
	__u16 val;

	/* Access the specified I2C bus. */
	if ((fd = open(device, O_RDWR)) == -1) {
		printf("FAIL\nI2C test failed opening %s: %s\n", \
				device, strerror(errno));
		return FD_NO_OPEN;
	}

	addr = (int) strtol(i2c_addr, NULL, 16);
	/* Set I2C slave address.  */
	if (ioctl(fd, I2C_SLAVE, addr) < 0) {
		printf("FAIL\nI2C Address set Fail. Error on ioctl: %s\n",
				strerror(errno));
		return I2C_NO_DEVICE;
	}

	reg = (__u8) strtol(i2c_reg, NULL, 16);
	/* Tell I2C device which register to report */
	if (i2c_write_byte(fd, reg) == -1) {
		printf("FAIL\nI2C Register request failed. Error on ioctl: \
				%s\n", strerror(errno)); 
		return I2C_NO_WRITE;
	}

	/* Figure out to read 1 or 2 bytes */
	num_bytes = strlen(expected_value);
	if ((num_bytes != 2) && (num_bytes != 4)) {
		printf("FAIL\nI2C Invalid expected value: %s\n",
				expected_value);
		return INVALID_ARG;
	}
	
	/* Read first byte. */
	if (i2c_read_byte(fd, &b) == -1) {
		printf("FAIL\nI2C Read byte failed. Error on ioctl: %s\n",
				strerror(errno)); 
		return I2C_NO_READ;
	}
	val = (__u16)b;

	if (num_bytes == 4) {
		/* Read second byte. */
		if (i2c_read_byte(fd, &b) == -1) {
			printf("FAIL\nI2C Read byte failed. Error on ioctl: \
					%s\n", strerror(errno)); 
			return I2C_NO_READ;
		}
		/* Combine with first byte. */
		val <<= 8;
		val += (__u16)b;
	} 

	/* Compare read value against expected value. Convert both to int, then
	 * perform simple comparison of their values.
	 */
	errno = 0;
	expected = (int) strtol(expected_value, NULL, 16);
	if (errno) {
		printf("FAIL\nI2C Invalid expected value %s\n", expected_value);
		return INVALID_ARG;
	}

	actual = (int) val;
	if (expected != actual) {
		printf("FAIL\nI2C Actual: 0x%X, Expected: 0x%X\n", val,
				expected);
		return I2C_ACT_V_EXP;
	}

	return SUCCESS;
}

