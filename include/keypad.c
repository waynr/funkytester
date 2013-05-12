/**
 * Keypad interface functions.
 *
 * Copyright (C) 2009 EMAC, Inc.
 */
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include "keypad.h"

int setup_keypad(void)
{
	int fd;
	static char matrix[KEYPAD_ROWS * KEYPAD_COLUMNS] = { 
		'1', '2', '3', 'x', 'x', 'x',
		'4', '5', '6', 'x', 'x', 'x',
		'7', '8', '9', 'x', 'x', 'x',
		'*', '0', '#', 'x', 'x', 'x' };

	if ((fd = open("/dev/keypad0", O_RDONLY | O_NONBLOCK)) <= 0)
		return -1;

	/* load the matrix */
	ioctl(fd, SETKEYARRAY, (unsigned long)matrix);
	return fd;
}

int read_keypad(int fd)
{
	char c;
	if (read(fd, &c, 1) == 1)
		return c;
	/* no character available */
	return -1;
}

