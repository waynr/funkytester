#include <stdio.h>
#include <termios.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <poll.h>
#include <unistd.h>

int setup_serial(int fd, int baud, int handshake)
{
	struct termios newtio;
	tcgetattr(fd, &newtio);
	tcflag_t       cflags;

	cflags  = 0;
	cflags |= CREAD;   // receiver enable
	if (handshake)
		cflags |= CRTSCTS;
	else
		cflags |= CLOCAL;  // local mode
	cflags &= ~PARENB; // no parity
	cflags &= ~CSTOPB; // only one stop bit
	cflags &= ~CSIZE;  // mask char-size bits
	cflags |= CS8;     // 8 bits
	cflags |= baud;    // baud parameter

	newtio.c_lflag &= ~(ICANON|ECHO);
	newtio.c_iflag &= ~(IXON|ICRNL);
	newtio.c_oflag &= ~(ONLCR);
	newtio.c_cflag = cflags;
	
	newtio.c_cc[VMIN] = 1;
	newtio.c_cc[VTIME] = 0;
	tcflush(fd, TCIOFLUSH); // Flush the device buffer
	tcsetattr(fd, TCSANOW, &newtio);

	return 0;
}


int poll_serial(int fd)
{
	struct pollfd fds[1];
	fds[0].fd = fd;
	fds[0].events = POLLIN;

	switch (poll(fds, 1, 1000))
	{
		case 0: /* timeout */
			return 0;
			break;
		case -1: /* poll error */
			return -1;
			break;
		default:
			if (fds[0].revents & POLLIN)
			{
				return 1;
			}
			/* non input event */
			return -1;
			break;
	}
	return -1;
}
