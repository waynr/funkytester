#ifndef RS485_H_
#define RS485_H_

#ifndef PORT_485 
#define PORT_485 "/dev/ttyS1"
#endif

#ifndef CONTROL_FILE 
#define CONTROL_FILE "/dev/rtsctl"
#endif

#ifndef RTS_COMMAND  
#define RTS_COMMAND  0x1
#endif

#ifndef BAUD 
#define BAUD B9600
#endif

#ifndef BUFF_485 
#define BUFF_485 1024
#endif

int init_485(char *);

#endif /*RS485_H_*/
