#ifndef _KEYPAD_H_
#define _KEYPAD_H_

int setup_keypad(void);
int read_keypad(int fd);

#define KEYROW		0x03
#define KEYCOLUMN	0x70
#define KEYGATE		0x04
#define ROWCOLMASK	(KEYROW|KEYCOLUMN)

#define ROW(pos)		((~pos)&KEYROW)
#define COLUMN(pos) 		(pos>>4)
#define KEYPAD_ROWS		4
#define KEYPAD_COLUMNS  	6
#define DRIVERCODE 		'K'
#define SETKEYARRAY		_IOR(DRIVERCODE,0,char)
#define GETKEYARRAY 		_IOW(DRIVERCODE,1,char)
#define KEYPAD_UNDEFINED_CHAR	'x'

#endif /*_KEYPAD_H_*/
