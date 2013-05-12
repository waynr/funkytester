#ifndef GPIO_CHAR_H_
#define GPIO_CHAR_H_

/* Userspace version of kernel header file */

#include <linux/ioctl.h>

#define RTDM_CLASS_GPIO 0x80 

/* standard read/write functions */
#define DDRREAD         _IOR(RTDM_CLASS_GPIO,0,char)
#define DDRWRITE        _IOW(RTDM_CLASS_GPIO,0,char)
#define DATAREAD        _IOR(RTDM_CLASS_GPIO,1,char)
#define DATAWRITE       _IOW(RTDM_CLASS_GPIO,1,char)
#define INDEXREAD       _IOR(RTDM_CLASS_GPIO,2,char)
#define INDEXWRITE      _IOW(RTDM_CLASS_GPIO,2,char)

/* nolock functions */
#define DDRREAD_NL	_IOR(RTDM_CLASS_GPIO, 3, char)
#define DDRWRITE_NL 	_IOW(RTDM_CLASS_GPIO, 3, char)
#define DATAREAD_NL	_IOR(RTDM_CLASS_GPIO, 4, char)
#define DATAWRITE_NL	_IOW(RTDM_CLASS_GPIO, 4, char)
#define INDEXREAD_NL	_IOR(RTDM_CLASS_GPIO, 5, char)
#define INDEXWRITE_NL	_IOW(RTDM_CLASS_GPIO, 5, char)

/* lock/unlock */
#define GPIOLOCK	_IO( RTDM_CLASS_GPIO, 6)
#define GPIOUNLOCK	_IO( RTDM_CLASS_GPIO, 7)

#endif /*GPIO_CHAR_H_*/
