#!/usr/bin/env python3

# https://github.com/HubCityLabs/py532lib
# sudo apt install python3 python3-requests
# mo/sda/tx -> raspi pyhsical 3
# nss/sclk/rx -> raspi physical 5
# Logs at sudo journalctl -u readnfc

import requests
import os.path
import sys
import binascii
import time
from subprocess import call
from py532lib.py532lib.constants import *
from py532lib.py532lib.frame import *
from py532lib.py532lib.i2c import *
from parseconfig import parseConfig

# holds config settings
config = []


def log(message=''):
    print(message)
    sys.stdout.flush()


def refresh_list():
    if 0 == len(config['readnfc']['tagurl']):
        return False

    r = requests.get(config['readnfc']['tagurl'], allow_redirects=True)
    open(config['readnfc']['tagurl'], 'wb').write(r.content)
    return True


def report_card(cardid=''):
    if 0 == len(config['readnfc']['tagurl']):
        return False

    requests.get(config['readnfc']['tagurl'] +
                 '?id=' + cardid, allow_redirects=True)
    return True


def read_cards():
    log('Reading tag list ' + config['readnfc']['tagurl'])

    with open(config['readnfc']['tagurl'], 'r') as f:
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
    return tags


def stop_volumio():
    log('Stoping any music currently playing')
    call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)
    call(['/usr/bin/mpc', '-q', 'stop'])  # This shouldn't be necessary, but...
    # time.sleep(0.1)


def get_cardid():
    binarycard_data = pn532.read_mifare().get_data()
    hexcard_data = binascii.hexlify(binarycard_data).decode()
    log('Card data: %s / %s' % (str(binarycard_data), hexcard_data))
    return hexcard_data


def play_feedback():
    log('Play audio feedback.')  # file needs to be in local music archive:

    if len(config['readnfc']['feedbackfile']) and os.path.isfile('/' + config['readnfc']['feedbackfile']):
        # call(['/usr/local/bin/node', '/volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js',
        #       'mpd', config['readnfc']['feedbackfile']])
        # call(['mpc insert', config['readnfc']['feedbackfile']])
        # call(['mpc play'])
        play_volumio('mpd', config['readnfc']['feedbackfile'])
        time.sleep(1)
        call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)


def play_volumio(mediatype, uri):

    log('Play selected source ' + type + ' ' + uri)
    if type == 'spop':
        call('/usr/local/bin/node /volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js ' +
             type + ' ' + uri + ' &', shell=True)
    elif type == 'mpd' or type == 'webradio':
        call(['mpc insert', uri])
        call(['mpc play'])
    elif type == 'cmd':
        call(['mpc', uri])


if __name__ == '__main__':     # Program start from here
    config = parseConfig('settings.ini')
    if (config == []):
        log(message='Error missing settings.ini')
        sys.exit(1)

    # Init
    pn532 = Pn532_i2c()
    pn532.SAMconfigure()

    if refresh_list():
        log(message='Updated list from %s.' % config['readnfc']['tagurl'])
    tags = read_cards()

    while True:
        try:
            hexcard_data = get_cardid()

            # Loop list of tags in search for the one scanned
            found_card = False
            for name, nfcid in tags.items():
                if hexcard_data == nfcid:  # Found!
                    mediatype, uri = name.split(',')
                    found_card = True

                    if (mediatype != 'cmd'):
                        stop_volumio()
                        play_feedback()

                    play_volumio(mediatype, uri)
                    time.sleep(5)  # Keep same card from being read again

                    break  # Stop searching

            if not found_card:
                report_card(hexcard_data)

        except KeyboardInterrupt:
            sys.exit(0)
