#ifndef GPIO_H_
#define GPIO_H_

#include <asm/types.h>

static inline int gpio_dev_open(const char *dev)
{
    return open(dev, O_RDWR);
}

__u32 gpio_read_index(__u32 index, int fd);
__u32 gpio_write_index(__u32 index, __u32 val,  int fd);
__u32 gpio_read(int fd);
__u32 gpio_write(__u32 val,  int fd);

#endif /* GPIO_H_ */
