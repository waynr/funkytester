/**
 * general GPIO access functions
 */

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <asm/types.h>
#include <sys/ioctl.h>

#include "gpio_char.h"

__u32 gpio_lock(int fd)
{
	if (ioctl(fd, GPIOLOCK, NULL) == -1) {
		fprintf(stderr, "Error locking GPIO port\n");
		return -1;
	}
	return 0;
}

__u32 gpio_unlock(int fd)
{
	if (ioctl(fd, GPIOUNLOCK, NULL) == -1) {
		fprintf(stderr, "Error unlocking GPIO port\n");
		return -1;
	}
	return 0;
}

__u32 gpio_read_index(__u32 index, int fd)
{
    __u32 val;
    
    if (ioctl(fd, INDEXWRITE, &index) == -1) {
        fprintf(stderr, "Error writing index on GPIO port\n");
        return -1;
    }
    if (ioctl(fd, DATAREAD, &val) == -1) {
        fprintf(stderr, "Error reading data on GPIO port\n");
        return -1;
    }
    return val;
}

__u32 gpio_read_index_nl(__u32 index, int fd)
{
    __u32 val;
    
    if (ioctl(fd, INDEXWRITE_NL, &index) == -1) {
        fprintf(stderr, "Error writing index on GPIO port\n");
        return -1;
    }
    if (ioctl(fd, DATAREAD_NL, &val) == -1) {
        fprintf(stderr, "Error reading data on GPIO port\n");
        return -1;
    }
    return val;
}

__u32 gpio_write_index(__u32 index, __u32 val,  int fd)
{
    if (ioctl(fd, INDEXWRITE, &index) == -1) {
        fprintf(stderr, "Error writing index on GPIO port\n");
        return -1;
    }

   if (ioctl(fd, DATAWRITE, &val) == -1) {
        fprintf(stderr, "Error writing data on GPIO port\n");
        return -1;
    }
   return 0;
}

__u32 gpio_write_index_nl(__u32 index, __u32 val,  int fd)
{
    if (ioctl(fd, INDEXWRITE_NL, &index) == -1) {
        fprintf(stderr, "Error writing index on GPIO port\n");
        return -1;
    }

   if (ioctl(fd, DATAWRITE_NL, &val) == -1) {
        fprintf(stderr, "Error writing data on GPIO port\n");
        return -1;
    }
   return 0;
}

__u32 gpio_read(int fd)
{
    __u32 val;
    
    if (ioctl(fd, DATAREAD, &val) == -1) {
        fprintf(stderr, "Error reading data on GPIO port\n");
        return -1;
    }
    return val;
}

__u32 gpio_read_nl(int fd)
{
    __u32 val;
    
    if (ioctl(fd, DATAREAD_NL, &val) == -1) {
        fprintf(stderr, "Error reading data on GPIO port\n");
        return -1;
    }
    return val;
}

__u32 gpio_write(__u32 val,  int fd)
{

   if (ioctl(fd, DATAWRITE, &val) == -1) {
        fprintf(stderr, "Error writing data on GPIO port\n");
        return -1;
    }
   return 0;
}

__u32 gpio_write_nl(__u32 val,  int fd)
{

   if (ioctl(fd, DATAWRITE_NL, &val) == -1) {
        fprintf(stderr, "Error writing data on GPIO port\n");
        return -1;
    }
   return 0;
}

