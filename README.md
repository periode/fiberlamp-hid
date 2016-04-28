# Illuminator Interface

## API for interfacing with the Fiberlamp Illuminator over HID

This repository contains a simple python script providing different endpoints in order to control the color setting of a Fiberlamp via OSC.

## illuminator.py Overview

The main script is illuminator.py and contains different endpoints:
* /change r g b (int int int) sets the color from the current value to the target value immediately

* /color r g b t (int int int float) changes the color from the current value to the target value over t seconds

* /heartbeat r g b t (int int int float) will pulsate from the current color to the target color over t seconds and back

* /black will set the color to black, essentially turning off the lamp

* /blink d t will start blinking the color


## dependencies

This script requires the following python modules:
* [cython-hid](https://github.com/trezor/cython-hidapi)
* [pyOSC](https://trac.v2.nl/wiki/pyOSC)


## additional scripts

In order to test out communcation, this repo includes:
* osc_client.js, an osc client in node.js
* osc_client.maxpat, an osc client in max/msp
