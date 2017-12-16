#!/usr/bin/env python3

# https://github.com/HubCityLabs/py532lib
# sudo apt install libnfc5 libnfc-bin libnfc-examples python3
# /etc/nfc/libnfc.conf must contain:
# device.name = "PN532 over I2C"
# device.connstring = "pn532_i2c:/dev/i2c-1"
# mo/sda/tx -> raspi pyhsical 3
# nss/sclk/rx -> raspi physical 5
# test nfc reader with sudo i2detect -y 1
# Logs at sudo journalctl -u readnfc

tagfile='readnfc.list'

from py532lib.i2c import *
from py532lib.frame import *
from py532lib.constants import *
from subprocess import call
import time
import binascii
import sys

def log(message=''):
    print (message)
    sys.stdout.flush()

pn532 = Pn532_i2c()
pn532.SAMconfigure()

log('Reading tag list ' + tagfile)

# Read tag list
with open(tagfile, 'r') as f:
    tagdata = f.read()

tags = {}
for tagline in tagdata.split('\n'):
    if tagline.startswith('#') or \
       tagline.startswith(' ') or \
       0 == len(tagline):
        continue

    serviceuri = tagline.split(';')[0]
    tag = tagline.split(';')[1]
    tags[serviceuri] = tag

log(str(len(tags)) + ' tags in store. Ready to read.')

while True:
    binarycard_data = pn532.read_mifare().get_data()
    hexcard_data = binascii.hexlify(binarycard_data).decode()
    log('Card data: %s / %s' % (str(binarycard_data), hexcard_data))
    
    log('Stoping any music currently playing')
    call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)
    call(['/usr/bin/mpc', '-q', 'stop']) # This shouldn't be necessary, but...
    #time.sleep(0.1)

    # Loop list of tags in search for the one scanned
    for name, nfcid in tags.items():
        if hexcard_data == nfcid: # Found!
            log('Play audio feedback.') # file needs to be in local music archive:
            call(['/usr/local/bin/node', '/volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js', 'mpd', 'mnt/INTERNAL/thankyouk.mp3'])
            time.sleep(1)
            call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)

            type, uri = name.split(',')
            log(type + ' ' + uri)

            log('Play selected source ' + type + ' ' + uri)
            call(['/usr/local/bin/node', '/volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js', type, uri])
            break # Stop searching
    time.sleep(5) # Keep same card from being read again

