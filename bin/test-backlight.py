#!/usr/bin/python

import time, threading

def dimmer(backlight, reverse=False, timeout=0.05, ):
    values = range(backlight["min"], backlight["max"], backlight["step"])
    if reverse:
        values.reverse()
    with open(backlight["file"], 'w+') as f:
        for i in values:
            f.write(str(i))
            f.flush()
            time.sleep(timeout)

def loop_brightness(backlight):
    while True:
        dimmer(backlight)
        dimmer(backlight, reverse=True)

if __name__ == "__main__":
    bl = {
        "file" : "/sys/class/backlight/backlight/brightness",
        "min" : 5,
        "max" : 50,
        "step" : 1,
        }

    if True:
        loop_brightness(bl)
    else:
        thread = threading.Thread(target=loop_brightness, args=[bl])
        thread.daemon = True
        thread.start()
        time.sleep(15)
