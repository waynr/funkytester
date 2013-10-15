
/**
 * Error code definitions. These are the codes that the various testing
 * functions should produce to indicate success or failure.
 */

/* Guidelines For Creating New Error Codes
 *  To facilitate the smooth function of the EMAC Test API, it would be a good
 *  idea to keep some of the following principles in mind when adding new error
 *  codes:
 *   * when adding new error codes, add them under an existing category if it
 *   makes sense to do so. 
 *   * 1-63 are generic error codes that could occur in more than one type of
 *   test (file does not exist, will not open, etc). these types of errors 
 *   might indicate that a kernel module is not loading for whatever reason, 
 *   or maybe the file permissions are bad, who knows what.
 *   * sometimes it makes sense to split a 32-code category in two such as when
 *   the POWER_OUTPUT category was inserted into the middle of the SERIAL_PORT
 *   category (because at the time it seemed like neither category would ever
 *   have more than 16 different error types)
 */

#define	SUCCESS		0
 #define FD_NO_OPEN	1
 #define FD_NO_WRITE	2
 #define FD_NO_READ	3
 #define BUF_CMP_FAIL	4	/* A comparison was made between two buffers (the 
				   contents of a file written compared to the same file
				   read, for instance) */
 #define TIMEOUT	5
 #define INVALID_ARG	6

#define BLOCK_DEV	64
#define BLOCK_NO_MOUNT	65
//   fs-specific
//   device-specific

#define SERIAL		96
 #define SERIAL_WRITE	97
 #define SERIAL_READ	98
 #define SERIAL_POLL	99

#define POWER_OUTPUT	112	/* General power output error */

#define RS485		128
 #define RS485_INIT	129

#define RS422		160

#define PLD_GEN		192
 #define PLD_DIR_MIS	193	/* Specified sysfs PLD directory is missing */ 
 #define PLD_NOT_DIR	194	/* Specified sysfs PLD directory is not a 
				   directory! */ 

#define RTC		224
 #define RTC_TOD	225
 #define RTC_NO_SET	226
 #define RTC_NO_GET	227

#define ANALOG		256
 #define  ATOD_FAIL	257
 #define  SPI_FAIL	258

#define Audio		288

#define ETHERNET	320
 #define ETH_SYSFS	321	/* Specified ping destination unreachable */
 #define ETH_L_SPEED	322	/* Insufficient link speed, possible cold 
				   solder joints */
 #define ETH_NO_I_UP	323	/* No interfaces currently up. */
 #define ETH_PING_DEST	324	/* Specified ping destination unreachable */

#define GPIO		352
 #define GPIO_BAD_VAL	353	/* Specified value incorrect */
 #define GPIO_NO_WRITE	354	/* Failed GPIO Write */
 #define GPIO_NO_READ	355	/* Failed GPIO Read */

#define PWM		384
 #define PWM_NO_WWRITE	385	/* PWM no WIDTHUSWRITE */

#define I2C		416
 #define I2C_NO_DEVICE	417	/* I2C set address fails */
 #define I2C_NO_READ	418	/* I2C read fails */
 #define I2C_NO_WRITE	419	/* I2C write fails */
 #define I2C_ACT_V_EXP	420	/* I2C write fails */

