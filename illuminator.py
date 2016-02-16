#dependencies cython-hid

import hid
import math
import time
from time import sleep
import noise
import socket, OSC, threading

receive_address = ('127.0.0.1', 7000) #Mac Adress, Outgoing Port

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

sending_data = False


#-------------------------CALCULATING CHECKSUM--------------------------------
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

#-------------------------LIST USB DEVICES--------------------------------
print "available usb devices:"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""

#"-------------------------SEND DATA--------------------------------"
def change_color(data):
    try:
        print "Opening device..."
        h = hid.device(vendor_id, product_id)
        print "Device opened!"

        while sending_data:#change it to "while the current color is not lerped all the way to the target color"
            print 'data ready to send %r' % data

            red = data[0]
            blue = data[1]
            green = data[2]
            transtion_time = [3]

            #so in order to do the transition,
            # i need to divide the difference of each values r, g, b by (deltatime * transitiontime)
            # and then add them at everyframe
            # and when they reach the difference set sending data to false


            blink = 0

            red = clamp(red)
            green = clamp(green)
            blue = clamp(blue)

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

def set_color(data):
    try:
        h = hid.device(vendor_id, product_id)
        print "device opened..."

        print 'setting new color to %r' % data
        red = clamp(data[0])
        blue = clamp(data[1])
        green = clamp(data[2])
        blink = 0

        data = [0x6, 0x1, red, green, blue, blink]
        checksum = -(twos_comp(sum_data_bytes(data))) % 256
        message = [header_byte] + data + [checksum, footer_byte]

        print "sending message: %r" % message
        h.write(message)

        print "Closing device"
        h.close()

    except IOError, ex:
        print ex


##########################
#	OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)

s.addDefaultHandlers()

def handle_root(addr, tags, stuff, source):
	print "---"
	print "received new osc msg from %s" % OSC.getUrlStr(source)
	print "with addr : %s" % addr
	print "typetags %s" % tags
	print "data %s" % stuff
	print "---"

def handle_change(addr, tags, data, source):
    print "---"
    print "handling change from %s" % OSC.getUrlStr(source)
    print "with addr %s" % addr
    print "tags %s" % tags
    print "data %s" % data
    print "---"

    sending_data = True
    change_color(data)

def handle_color(addr, tags, data, source):
    print "---"
    print "handling color from %s" % OSC.getUrlStr(source)
    print "with addr %s" % addr
    print "tags %s" % tags
    print "data %s" % data
    print "---"

    sending_data = True
    set_color(data)

def handle_heartbeat(addr, tags, data, source):
    print "---"
    print "handling color from %s" % OSC.getUrlStr(source)
    print "with addr %s" % addr
    print "tags %s" % tags
    print "data %s" % data
    print "---"

    sending_data = True
    pulse(data)

print "endpoints:"
print "---"
print "/change r g b t ---- changes the color to the specified rgb values over t seconds"
print "/color r g b ---- changes the color immediately"
print "/heartbeat"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/heartbeat', handle_heartbeat)

print "Registered Callback-functions are :"
for addr in s.getOSCAddressSpace():
	print addr

# Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()

#Threads
try :
	while 1 :
		time.sleep(10)

except KeyboardInterrupt :
	print "\nClosing OSCServer."
	s.close()
	print "Waiting for Server-thread to finish"
	st.join()
	print "Done"


print "Lights off!"
