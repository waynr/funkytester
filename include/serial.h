#ifndef SERIAL_H_
#define SERIAL_H_

int setup_serial(int fd, int baud, int handshake);
int poll_serial(int fd);

#endif /*SERIAL_H_*/
