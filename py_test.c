/**
j* SoM-9M10 functional test
 * !tstrat
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

#include "include/emac_generic_tests.h"

int main(int argc, char *argv[])
{
	int failed = 0;
	char *first_arg;
	int retval = 0;

	first_arg = argv[1];

	/* imagine how much nicer this would be with the guards and pattern
	 * matching of Haskell...
	 */
	
	if (strcmp(first_arg, "serial_test") == 0) {
		if (argc > 4 || argc < 3) {
			fprintf(stderr,"Usage: %s %s <dir1> [dir2]\n", 
					argv[0],first_arg);
			exit(EXIT_FAILURE);
		} else if (argc == 4) {
			retval = test_serial(argv[2],argv[3]);
		} else if (argc == 3) {
			retval = test_serial(argv[2],argv[2]);
		}
	} else if (strcmp(first_arg, "mcp3208_analog_test") == 0) {
		if (argc > 5 || argc < 2) {
			fprintf(stderr,"Usage: %s %s [file [num [dialog]]]\n", 
					argv[0],first_arg);
			exit(EXIT_FAILURE);
		} else if (argc == 5) {
			retval = test_analog_mcp3208(argv[2],argv[3],argv[4]);
		} else if (argc == 4) {
			retval = test_analog_mcp3208(argv[2],argv[3],DIALOG);
		} else if (argc == 3) {
			retval = test_analog_mcp3208(argv[2],NULL,DIALOG);
		} else {
			retval = test_analog_mcp3208(NULL,NULL,DIALOG);
		}
	} else if (strcmp(first_arg, "gpio_analog_test") == 0) {
		if (argc > 5 || argc < 2) {
			fprintf(stderr,"Usage: %s %s [file [num [dialog]]]\n", 
					argv[0],first_arg);
			exit(EXIT_FAILURE);
		} else if (argc == 5) {
			retval = test_analog_gpio(argv[2],argv[3],argv[4]);
		} else if (argc == 4) {
			retval = test_analog_gpio(argv[2],argv[3],DIALOG);
		} else if (argc == 3) {
			retval = test_analog_gpio(argv[2],NULL,DIALOG);
		} else {
			retval = test_analog_gpio(NULL,NULL,DIALOG);
		}
	} else if (strcmp(first_arg, "pld_test") == 0) {
		if (argc == 2) {
			retval = test_pld(NULL);
		} else if (argc > 3) {
			fprintf(stderr,"Usage: %s %s [device file]\n",argv[0],
					first_arg);
			exit(EXIT_FAILURE);
		} else {
			retval = test_pld(argv[2]);
		}
	} else if (strcmp(first_arg, "rtc_test") == 0) {
		if (argc == 2) {
			retval = test_rtc(NULL);
		} else if (argc > 3) {
			fprintf(stderr,"Usage: %s %s [device file]\n",argv[0],
					first_arg);
			exit(EXIT_FAILURE);
		} else {
			retval = test_rtc(argv[2]);
		}
	} else if (strcmp(first_arg, "block_device_test") == 0) {
		if (argc != 3) {
			fprintf(stderr,"Usage: %s %s <dir1>\n",argv[0],first_arg);
			exit(EXIT_FAILURE);
		}
		retval = test_block(argv[2]);
	} else {
		printf("Fail, please try again.\n");
		failed = 1;
	}

	return retval;
}

