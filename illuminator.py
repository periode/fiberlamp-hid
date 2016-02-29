#dependencies
# --cython-hid
# --OSC

import hid
import math
import time
from time import sleep
import noise
import socket, OSC, threading

#IP Adress and outgoing port to listen on
receive_address = ('127.0.0.1', 7000)

header_byte = 0xa9
footer_byte = 0x5c

#specific to the lamp used
vendor_id = 0x24c2
product_id = 0x1306

#starting values are black. blink should not change (0 = constant)
red = 0
green = 0
blue = 0
blink = 0

#time variables for timed transition
current_time = 0.0
previous_time = 0.0
delta_time = 0.0


#-------------------------HELPER METHODS--------------------------------
#compute the 2's compliment of int value val
def twos_comp(val):
    if (val & (1 << (7))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << 8)        # compute negative value
    return val                         # return positive value as is

#convert from int to byte
def tobyte(data):
    return bytes(bytearray([data]))

#sum a given array of bytes
def sum_data_bytes(message):
    total = sum(message)
    mod = total % 256

    return mod

#clamp a vale between 0 and 255 and returns as integer
def clamp(val):
    return max(min(255, int(val)), 0)

#ramp a value from a to b over t seconds
def ramp(a, b, t, delta):
    i = max (a, b)

    if t < 1:
        t = t*t

    if a < b:
        a = a + ((delta*i)/t)
    else:
        a = a - ((delta*i)/t)

    return a

#-------------------------LIST USB DEVICES--------------------------------
print "available usb devices:"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""



#---------------------SEND COLOR TO DEVICE-------------------------------
def send_color():
    global red
    global green
    global blue
    global blink

    try:
        illuminator = hid.device(vendor_id, product_id)

        data = [0x6, 0x1, red, green, blue, blink]
        checksum = -(twos_comp(sum_data_bytes(data))) % 256
        message  = [header_byte] + data + [checksum, footer_byte]
        illuminator.write(message)

        illuminator.close()
    except IOError, ex:
        print ex
        illuminator.close()


#-------------------------COLOR METHODS--------------------------------
#heartbeat ramps from the current color to the target color over t seconds, then ramps back down to the starting color
def heartbeat(data):
    global red
    global green
    global blue

    global current_time
    global previous_time
    global delta_time

    start_time = time.clock()

    start_r = red
    start_g = green
    start_b = blue

    target_r = data[0]
    target_g = data[1]
    target_b = data[2]

    t = data[3]

    print "setting heartbeat to %r %r %r over %r second(s)" % (target_r, target_g, target_b, t)

    temp_r = red
    temp_g = green
    temp_b = blue

    thresh = 2

#ramp value up
    while (abs(temp_r - target_r) > thresh) or (abs(temp_g - target_g) > thresh) or (abs(temp_b - target_b) > thresh):
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time

        temp_r = ramp(temp_r, target_r, t, delta_time)
        temp_g = ramp(temp_g, target_g, t, delta_time)
        temp_b = ramp(temp_b, target_b, t, delta_time)

        red = clamp(temp_r)
        green = clamp(temp_g)
        blue = clamp(temp_b)

        send_color()

#ramp value down
    while (abs(temp_r - start_r) > thresh) or (abs(temp_g - start_g) > thresh) or (abs(temp_b - start_b) > thresh):
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time

        temp_r = ramp(temp_r, start_r, t, delta_time)
        temp_g = ramp(temp_g, start_g, t, delta_time)
        temp_b = ramp(temp_b, start_b, t, delta_time)

        red = clamp(temp_r)
        green = clamp(temp_g)
        blue = clamp(temp_b)

        send_color()


    stop_time = time.clock()

    print 'heartbeat set over %r second(s)' % ((stop_time - start_time))

#changes the current color to the target color r g b over t seconds
def change_color(data):
    global red
    global green
    global blue

    global current_time
    global previous_time
    global delta_time

    start_time = time.clock()

    target_r = data[0]+1
    target_g = data[1]+1
    target_b = data[2]+1
    t = data[3]

    thresh = 2

    temp_r = red
    temp_g = green
    temp_b = blue

    print "changing color to %r %r %r over %r seconds..." % (target_r, target_g, target_b, t)

    while (abs(temp_r - target_r) > thresh) or (abs(temp_g - target_g) > thresh) or (abs(temp_b - target_b) > thresh):
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time

        temp_r = ramp(temp_r, target_r, t, delta_time)
        temp_g = ramp(temp_g, target_g, t, delta_time)
        temp_b = ramp(temp_b, target_b, t, delta_time)

        red = clamp(temp_r)
        green = clamp(temp_g)
        blue = clamp(temp_b)

        send_color()

    stop_time = time.clock()
    print "...changed color over %r seconds" % ((stop_time - start_time))

#jump to the target color r g b
def set_color(data):
    global red
    global green
    global blue
    global blink

    print 'setting new color to %r' % data
    red = clamp(data[0])
    green = clamp(data[1])
    blue = clamp(data[2])
    blink = 0

    send_color()



##########################
#	OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)

s.addDefaultHandlers()

#default handler prints out the message
def handle_root(addr, tags, data, source):
	print "---"
	print "received new osc msg from %s" % OSC.getUrlStr(source)
	print "with addr : %s" % addr
	print "typetags %s" % tags
	print "data %s" % data
	print "---"

def handle_change(addr, tags, data, source):
    change_color(data)

def handle_color(addr, tags, data, source):
    set_color(data)

def handle_heartbeat(addr, tags, data, source):
    heartbeat(data)

def handle_black(addr, tags, data, source):
    set_color([0, 0, 0])

print "endpoints:"
print "---"
print "/change r g b t ---- changes the color to the specified rgb values over t seconds"
print "/color r g b ---- changes the color immediately"
print "/heartbeat r g b t --- pulsates to the target color over t seconds"
print "/black --- turns off the lamp"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/heartbeat', handle_heartbeat)
s.addMsgHandler('/black', handle_black)

#Start OSCServer
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


print "...lights off!"
