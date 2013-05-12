#include <stdio.h>
#include <termios.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <unistd.h>

#include "rs485.h"
#include "gpio.h"

static int set_auto485(void);
static int setup_485(int fd);

/**
 * Function to open and initialize a serial port. 
 * @return -1 on failure, port file descriptor on success
 */
int init_485(char *dev)
{
    int port_fd;
    if ((port_fd = open(dev, O_RDWR | O_NOCTTY | O_NONBLOCK)) == -1) {
        printf("Error opening 485 port\n");
        return -1;
    }
    if (set_auto485() == -1) {
        printf("Error setting Auto485 toggle\n");
        return -1;
    }
    setup_485(port_fd);
    return port_fd;
}

/**
 * Function to turn on the auto-toggle function in the kernel driver
 * for the 485 port on the 9260.
 * @return -1 on error or 0 on success
 */
static int set_auto485(void)
{
    int control_fd;
    if ((control_fd = open(CONTROL_FILE, O_RDWR | O_SYNC)) == -1) {
        return -1;
    }
    
    gpio_write(RTS_COMMAND, control_fd);
    close(control_fd);

    return 0;
}

/**
 * Function to setup an open serial port.
 * @param fd the filedescriptor for the open tty
 * @return 0
 */
static int setup_485(int fd)
{
    /* set to 9600 baud, 1 stop bit, odd parity */
    struct termios newtio;
    tcgetattr(fd, &newtio);
    newtio.c_cflag = BAUD | CS8 | CREAD | PARENB | PARODD;
    newtio.c_cc[VTIME] = 0; // inter-character timer unused
    newtio.c_oflag = 0; // set for raw output
    newtio.c_lflag = 0; // set for non-canonical input processing
    newtio.c_iflag = IGNPAR;
    newtio.c_cc[VMIN] = 1; // blocking read until 1 character arrives
    tcflush(fd, TCIOFLUSH); // Flush the device buffer
    tcsetattr(fd, TCSANOW, &newtio);

    return 0;
}
