#!/usr/bin/env python3

# Inspired by https://volumio.org/forum/turn-led-when-volumio-ready-t5746.html

import subprocess
import sys
from time import sleep
from gpiozero import PWMLED
from parseconfig import parseConfig

# holds config settings
config = []

# pingserver = 'http://web.larsfp.clh.no/'
# pingserver = 'http://charon/'
led = PWMLED(18)


def log(message=''):
    print(message)
    sys.stdout.flush()


def setup():
    led.blink()  # Notify startup


def checkStatus():
    p = subprocess.Popen(
        '/usr/local/bin/volumio status',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    out, err = p.communicate()

    # print (status)
    # print(err)

    if 0 != p.returncode:
        led.blink()
        log("Status: error " + err.decode())
    elif 'play' in out.decode():
        # log("Status: playing")
        led.on()
    else:
        led.pulse()

    sleep(2)


def checkNetwork():
    p = subprocess.Popen(
        '/usr/bin/curl --silent ' + config['led']['pingserver'],
        stdout=subprocess.PIPE,
        shell=True
    )
    p.communicate()

    if 0 != p.returncode:
        led.blink()
        log('Status: network error, returncode ' + str(p.returncode))
        sleep(10)
        return False
    else:
        # log("Status: network OK.")
        return True


def destroy():
    led.off()


if __name__ == '__main__':  # Program start from here

    config = parseConfig('settings.ini')
    if (config == []):
        log(message='Error missing settings.ini')
        sys.exit(1)

    setup()

    try:
        count = 0
        while True:
            checkStatus()
            count += 1
            print("count", count, "%", count % 60)
            if 1 == count % 60:
                while not checkNetwork():
                    pass  # Keep testing until OK

    except KeyboardInterrupt:  # When 'CTRL+C' is pressed.
        destroy()
