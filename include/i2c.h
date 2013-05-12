/* i2c prototypes */
int i2c_set_slave(int fd, int addr);
int i2c_write_byte(int fd, __u8 byte);
int i2c_write_cmd(int fd, __u8 reg, __u8 cmd);
int i2c_read_byte(int fd, __u8 *val);
int i2c_read_reg(int fd, __u8 *val, __u8 reg);
