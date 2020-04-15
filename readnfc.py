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
#import py532lib
from subprocess import call
# from py532lib.py532lib.constants import *
# from py532lib.py532lib.frame import *
#from py532lib.py532lib.i2c import *
# from py532lib.py532lib.i2c import Pn532_i2c
# import py532lib
# from py532lib.frame import *
# from py532lib.i2c import *
# sudo pip3 install pn532pi
from pn532pi import Pn532, pn532
from pn532pi.interfaces.pn532i2c import Pn532I2c
# from pn532pi.interfaces.pn532spi import Pn532Spi
# from pn532pi.interfaces.pn532hsu import Pn532Hsu

from parseconfig import parseConfig

# holds config settings
# config = []
# holds all nfc tags
tags = {}


def log(message=''):
    print(message)
    sys.stdout.flush()


def refresh_list():
    if 0 == len(config['readnfc']['tagurl']):
        # skipping tag list update
        return False

    r = requests.get(config['readnfc']['tagurl'], allow_redirects=True)
    if 0 == len(r.content):
        log('Empty response from tagurl')
        return False

    f = open(config['readnfc']['tagfile'], 'wb')
    if f.mode == 'wb':
        f.write(r.content)
    else:
        log('Could not update local tag list ' + f.mode)
        f.close()
        return False
    f.close()
    return True


def report_card(cardid=''):
    log('Unknown card ' + cardid)
    if 0 == len(config['readnfc']['tagurl']):
        return False

    log('sending unknown card to reporturl')
    if 0 == len(config['readnfc']['reporturl']):
        requests.get(config['readnfc']['tagurl'] +
                     '/?id=' + cardid, allow_redirects=True)
    else:
        requests.get(config['readnfc']['reporturl'] +
                     cardid, allow_redirects=True)

    return True


def read_cards():
    log('Reading tag list ' + config['readnfc']['tagfile'])

    if 0 == len(config['readnfc']['tagfile']):
        log('Error missing local tag file')
        return False

    with open(config['readnfc']['tagfile'], 'r', encoding="utf-8") as f:
        tagdata = f.read()
    f.close()

    tags = {}
    for tagline in tagdata.split('\n'):
        if tagline.startswith('#') or \
                tagline.startswith(' ') or \
                0 == len(tagline):
            continue

        serviceuri = tagline.split(';')[0]
        tag = tagline.split(';')[1]
        tags[serviceuri] = tag

    log(str(len(tags)) + ' tags in store')
    return tags


def stop_volumio():
    log('Stoping any music currently playing')
    call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)
    call(['/usr/bin/mpc', '-q', 'stop'])  # This shouldn't be necessary, but...
    # time.sleep(0.1)


# def get_cardid():
#     log('get_cardid 1')
#     binarycard_data = pn532.read_mifare().get_data()
#     log('get_cardid 2')
#     hexcard_data = binascii.hexlify(binarycard_data).decode()
#     log('Card data: %s / %s' % (str(binarycard_data), hexcard_data))
#     return hexcard_data


def play_feedback():
    if len(config['readnfc']['feedbackfile']) and os.path.isfile('/' + config['readnfc']['feedbackfile']):
        log('Play audio feedback.')  # file needs to be in local music archive:

        # call(['/usr/local/bin/node', '/volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js',
        #       'mpd', config['readnfc']['feedbackfile']])
        # call(['mpc insert', config['readnfc']['feedbackfile']])
        # call(['mpc play'])
        play_volumio('mpd', config['readnfc']['feedbackfile'])
        time.sleep(0.5)
        call('/usr/local/bin/volumio clear > /dev/null 2>&1', shell=True)
    else:
        log('Skip audio feedback.')  # file needs to be in local music archive:


def play_volumio(mediatype, uri):
    log('Play selected source ' + mediatype + ' ' + uri)
    if mediatype == 'spop':
        log('call node')
        call('/usr/local/bin/node /volumio/app/plugins/system_controller/volumio_command_line_client/commands/addplay.js ' +
             mediatype + ' ' + uri + ' &', shell=True)
    elif mediatype == 'mpd' or mediatype == 'webradio':
        log('add to playlist')
        call('mpc insert ' + uri, shell=True)
        call(['mpc', 'play'])
    elif mediatype == 'cmd':
        log('send command')
        call(uri, shell=True)


def setup():
    global nfc
    global config
    global tags

    # test for settings.ini
    config = parseConfig('settings.ini')
    if (config == []):
        log(message='Error missing or empty settings.ini - see settings.ini.example')
        sys.exit(1)

    # test for mpc
    mpc_result = call(['mpc', 'status'])
    if (mpc_result != 0):
        log(message='Error missing mpc command - check if volumio is setup correctly on the device')
        sys.exit(1)

    # update nfc code list
    if refresh_list():
        log(message='Updated local tag list from %s' %
            config['readnfc']['tagurl'])

    # test for nfc code list
    tags = read_cards()
    if tags == False:
        log('Error no tags from local tag file read')
        sys.exit(1)

    # test for nfc reader
    log('Initialize i2c...')
    # pn532 = Pn532_i2c()
    PN532_I2C = Pn532I2c(1)
    # log('config')
    # pn532.SAMconfigure()
    log('Initialize NFC reader...')
    nfc = Pn532(PN532_I2C)
    # log('refresh list')

    log('Get NFC reader data...')
    nfc.begin()

    versiondata = nfc.getFirmwareVersion()
    if not versiondata:
        log("Didn't find PN53x board: " + str(versiondata))
        raise RuntimeError("Didn't find PN53x board")  # halt

    log('Set NFC reader configuration...')
    nfc.setPassiveActivationRetries(0xFF)
    nfc.SAMConfig()


def loop():
    #  Wait for an ISO14443A type cards (Mifare, etc.).  When one is found
    #  'uid' will be populated with the UID, and uidLength will indicate
    #  if the uid is 4 bytes (Mifare Classic) or 7 bytes (Mifare Ultralight)

    success, uid = nfc.readPassiveTargetID(
        pn532.PN532_MIFARE_ISO14443A_106KBPS)

    if (success):
        #  Display some basic information about the card

        # hexcard_data = binascii.hexlify(binarycard_data).decode()
        #     log('Card data: %s / %s' % (str(binarycard_data), hexcard_data))

        # print("Found an ISO14443A card")
        # print("UID Length: {:d}".format(len(uid)))
        hexcard_data = binascii.hexlify(uid).decode()
        print("UID Value: {}".format(hexcard_data))

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
            time.sleep(2)

        # binarycard_data = pn532.read_mifare().get_data()
        # hexcard_data = binascii.hexlify(binarycard_data).decode()
        # log('Card data: %s / %s' % (str(binarycard_data), hexcard_data))

    return False


# Program start from here
if __name__ == '__main__':

    setup()
    # waiting for input
    log('Waiting for card...')
    try:
        while True:
            if loop() == True:
                time.sleep(5)
                log('Waiting for card...')

    except KeyboardInterrupt:
        log('Good bye!')
        sys.exit(0)
    sys.exit(0)

    # while True:
    #     try:
    #         hexcard_data = get_cardid()

    #         # Loop list of tags in search for the one scanned
    #         found_card = False
    #         for name, nfcid in tags.items():
    #             if hexcard_data == nfcid:  # Found!
    #                 mediatype, uri = name.split(',')
    #                 found_card = True

    #                 if (mediatype != 'cmd'):
    #                     stop_volumio()
    #                     play_feedback()

    #                 play_volumio(mediatype, uri)
    #                 time.sleep(5)  # Keep same card from being read again

    #                 break  # Stop searching

    #         if not found_card:
    #             report_card(hexcard_data)
    #             time.sleep(2)

    #     except KeyboardInterrupt:
    #         sys.exit(0)
