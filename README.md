# Control Volumio.org using NFC

This is a collection of scripts to control a volumio based music player using a PN532 NFC reader. Idea from http://blog.zenona.com/ and http://tilman.de/projekte/audiosphere/.

See build log at https://0p.no/2017/12/19/volumio_nfc_build.html

## Idea

* Use NFC stickers or cards.
* When scanned, the id of the sticker is matched with a list. If contained in list, queue is cleared and selected music starts playing.
* Additional buttons are required for i.e. play/pause, next, volume up.
* Any music source can be used.
* Format of music list: see readnfc.list

## Setup

* Install Volumio on a Pi. Tested with version 2.323-2.344.
* i2c is already enabled.
* Connect NFC reader as advised, this script assumes i2c.
* Install requirements and a proper editor =) `sudo apt install python3 python3-requests python3-gpiozero vim-nox`
* Fetch https://github.com/HubCityLabs/py532lib
* Download this repo and run readnfc.py manually to test.
* To make it autostart, copy systemd service file readnfc.service to /etc/systemd/system/readnfc.service and enable: `sudo cp readnfc.service /etc/systemd/system/`
* Systemd timer to restart service soon after boot is needed for unknown reason. Also included. `sudo cp restartnfc.* /etc/systemd/system/`
* Reload and enable: `sudo systemctl daemon-reload; sudo systemctl enable readnfc.service; sudo systemctl enable restartnfc.timer`
* Add a script to add and play song to volumio: `sudo cp addplay.js /volumio/app/plugins/system_controller/volumio_command_line_client/commands/`
* Add a sound feedback file to music library, called: `thankyouk.mp3` so the path will be `mnt/INTERNAL/thankyouk.mp3`.

Optional:

* Suggested plugins for this setup:
  * Spotify Connect https://volumio.org/forum/volumio-plugins-collection-t6251.html#p30706
  * GPIO buttons https://volumio.org/forum/volumio-plugins-collection-t6251.html#p30812
* Led.py and led.service for adding a status LED.
* Thank me.

* rotary.py is to use a rotary encoder for next, previous.

## Debugging

For debugging the NFC reader, you can install libnfc5 and i2c-tools.

* Configure libnfc: `sudo mkdir /etc/nfc; sudo vim /etc/nfc/libnfc.conf`:

```bash
  device.name = "PN532 over I2C"
  device.connstring = "pn532_i2c:/dev/i2c-1"
```

* Test with `sudo i2detect -y 1` and `nfc-list` to make sure NFC reader is connected.

## Todo

* It would be very nice if all this could be turned into a proper volumio plugin.
* An easy way to store new tags?
* LED to notify when volumio is ready.
* LED to notify when volumio is broken (no wifi, shut down, etc)
* Better voice feedback.
