#dependencies cython-hid

import hid
import math
import time
from time import sleep
import noise

header_byte = 0xa9
footer_byte = 0x5c

vendor_id = 0x24c2
product_id = 0x1306

red = 0
green = 0
blue = 0
blink = 0

time_coeff = 100
color_coeff = 0
base_coeff = 0

def twos_comp(val):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (7))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << 8)        # compute negative value
    return val                         # return positive value as is

def tobyte(data):
    return bytes(bytearray([data]))

def sum_data_bytes(message):
    total = sum(message)
    mod = total % 256

    return mod

def clamp(val):
    return max(min(255, val), 0)

print "-------------------------LIST USB DEVICES--------------------------------"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""

print "-------------------------SEND DATA--------------------------------"
try:
    print "Opening device..."
    h = hid.device(vendor_id, product_id)
    print "Device opened!"

    while True:
        #set individual values
        red = int(math.cos(time.clock()*time_coeff)*color_coeff)+int(227*base_coeff)
        green = int(noise.pnoise1(time.clock()*time_coeff*2)*color_coeff)+int(57*base_coeff)
        blue = int(noise.pnoise1(time.clock()*time_coeff)*color_coeff)+int(57*base_coeff)
        blink = 0

        red = clamp(red)
        green = clamp(green)
        blue = clamp(blue)

        if color_coeff != 27:
            color_coeff += 0.5

        if base_coeff < 1:
            base_coeff += 0.00001


        data = [0x6, 0x1, red, green, blue, blink]
        checksum = -(twos_comp(sum_data_bytes(data))) % 256
        message = [header_byte] + data + [checksum, footer_byte]

        print "sending message: %r" % message
        h.write(message)

        d = h.read(255)
        print "received byte: %r\n" % bytes(bytearray(d))

    print "Closing device"
    h.close()

except IOError, ex:
    print ex
    print "You probably don't have the hard coded test hid. Update the hid.device line"
    print "in this script with one from the enumeration list output above and try again."

print "Lights off!"
