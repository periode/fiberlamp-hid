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

red = 100
green = 0
blue = 0
blink = 0

time_coeff = 100
color_coeff = 0
base_coeff = 0

current_time = 0.0
previous_time = 0.0
delta_time = 0.0

sending_data = True


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
    return max(min(255, int(val)), 0)

#-------------------------LIST USB DEVICES--------------------------------
print "available usb devices:"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""


#-------------------------TRANSITION OVER TIME--------------------------------
def heartbeat(data):
    global red
    global green
    global blue

    global current_time
    global previous_time
    global delta_time

    start_time = time.clock()

    target_r = data[0]
    target_g = data[1]
    target_b = data[2]
    t = data[3]

    print "setting heartbeat to %r %r %r over %r seconds" % (target_r, target_g, target_b, t)

    temp_r = red
    temp_g = green
    temp_b = blue

#ramp value up
    while red < target_r:
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time
        temp_r = temp_r + ((delta_time*target_r)/t)
        temp_g = temp_g + ((delta_time*target_g)/t)
        temp_b = temp_b + ((delta_time*target_b)/t)

        red = clamp(temp_r)
        green = clamp(temp_g)
        blue = clamp(temp_b)

        send_color()

#ramp value down
    while red > 0:
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time
        temp_r = temp_r - ((delta_time*target_r)/t)
        temp_g = temp_g - ((delta_time*target_g)/t)
        temp_b = temp_b - ((delta_time*target_b)/t)

        red = clamp(temp_r)
        green = clamp(temp_g)
        blue = clamp(temp_b)

        send_color()


    stop_time = time.clock()
    print 'completed in %r' % (stop_time - start_time)
    print 'transitioned lights to: r %r g %r b %r' % (red, green, blue)

#"-------------------------SEND DATA--------------------------------"
def change_color(data):
    global red
    global green
    global blue

    global current_time
    global previous_time
    global delta_time

    start_time = time.clock()

    target_r = data[0]
    target_g = data[1]
    target_b = data[2]
    t = data[3]

    if red < target_red:
        while red < target_r:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time
            red = red + ((delta_time*target_r)/t)
            green = green + ((delta_time*target_g)/t)
            blue = blue + ((delta_time*target_b)/t)
            send_color()
    else:
        while red > target_r:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time
            red = red - ((delta_time*target_r)/t)
            green = green - ((delta_time*target_g)/t)
            blue = blue - ((delta_time*target_b)/t)
            send_color()


def set_color(data):
    global red
    global green
    global blue
    global blink

    print 'setting new color to %r' % data
    red = clamp(data[0])
    blue = clamp(data[1])
    green = clamp(data[2])
    blink = 0

    send_color()


def send_color():
    global red
    global green
    global blue
    global blink

    try:
        illuminator = hid.device(vendor_id, product_id)

        # while sending_data:
        data = [0x6, 0x1, red, green, blue, blink]
        checksum = -(twos_comp(sum_data_bytes(data))) % 256
        message  = [header_byte] + data + [checksum, footer_byte]
        illuminator.write(message)

        illuminator.close()
    except IOError, ex:
        print ex
        illuminator.close()



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
    change_color(data)

def handle_color(addr, tags, data, source):
    set_color(data)

def handle_heartbeat(addr, tags, data, source):
    heartbeat(data)

print "endpoints:"
print "---"
print "/change r g b t ---- changes the color to the specified rgb values over t seconds"
print "/color r g b ---- changes the color immediately"
print "/heartbeat r g b t --- pulsates to the target color over t seconds"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/heartbeat', handle_heartbeat)

#Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()

#open HID device
# send_color()

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
