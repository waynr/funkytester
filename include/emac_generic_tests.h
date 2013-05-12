
/*
 * Copyright 2011 EMAC Inc
 *
 * Test library that should simplify the creation of new software testsets for
 * EMAC producets. 
 *
 */

#define F75111_SMBUS_ADDR 0x4E

#define JFFS2_TYPE	0x72b6
#define TMPFS_TYPE	0x01021994
#define NFS_TYPE	0x6969

/**
 * only close the second fd if it is defined and not equal to stdin
 */
#define close_fd(a,b) ({		\
	if ( b != 0 ) {			\
		close(b);		\
	}				\
	close(a);			\
})
int test_block(char *);

int test_serial(char *, char *);

/* PWM Testing functions and Setup */

#define PERIODUS 10000
#define PWM_DEFAULT "/dev/pwm"

int test_pwm(char *);

/* End PWM Testing functions and Setup */

#define PLD_DIR		"/sys/class/gpio/porta"
int test_pld(char *);

#define GPIO_PORT	"/dev/porta"
#define GPIO_PAT	0xAA
int test_gpio(char *, char *);

#define RTC_DEFAULT	"/dev/rtc0"
int test_rtc(char *);

#define PORT_485	"/dev/ttyS1"
#define CONTROL_FILE	"/sys/class/gpio/rtsctl/data"
#define RTS_COMMAND	"0x2"
#define BAUD		B301
#define BUFF_485	1024
int test_485(char *);

#define ADT7410_ADDR	0x48
int test_i2c_adt7410(char *,char *);

//#define NUM_ANALOG 11
#define NUM_SPI		8
#define NUM_GPIO	3
#define GPIO_DEV	"/dev/indexed_atod"
#define SPI_DEV		"/dev/mcp3208"
#define SLEEP_US	50000 /* 50 ms */
#define DIALOG		0

int test_analog_gpio(char *, char *, char *);
int test_analog_mcp3208(char *, char *, char *);

int test_gpo(char *, char *);
int test_gpi(char *, char *);

