#dependencies
# --cython-hid
# --OSC

import hid
import math
import time
from time import sleep
from noise import pnoise1
import socket, OSC, threading

#IP Adress and outgoing port to listen on
receive_address = ('127.0.0.1', 7000)

header_byte = 0xa9
footer_byte = 0x5c

#specific to the lamp used
vendor_id = 0x24c2
product_id = 0x1306

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
        a = a + 1
    else:
        a = a - 1

    return a



class Color:
    def __init__(self, r, g, b):
        self.r = clamp(r)
        self.g = clamp(g)
        self.b = clamp(b)

    def __str__(self):
        return "color(%i, %i, %i)" % (self.r, self.g, self.b)

    def ramp(self, color, duration, delta_time):
        r = ramp(self.r, color.r, duration, delta_time)
        b = ramp(self.b, color.b, duration, delta_time)
        g = ramp(self.g, color.g, duration, delta_time)
        return Color(r, g, b)

    def distance(self, other):
        return max(max(abs(self.r - other.r), abs(self.g - other.g)), abs(self.b - other.b))


BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)



class Illuminator:
    def __init__(self, path):
        self.path = path
        self.color = BLACK
        self.connection = hid.device(None, None, path)
        self.connection.set_nonblocking(1)
        self.turn_off()

    def close(self):
        self.connection.close()

    def turn_off(self):
        self.set(BLACK)

    def set(self, color):
        try:
            data = [0x6, 0x1, color.r, color.g, color.b, 0]
            checksum = -(twos_comp(sum_data_bytes(data))) % 256
            message  = [header_byte] + data + [checksum, footer_byte]
            self.connection.write(message)

        except IOError, ex:
            print ex
            self.connection.close()





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

    print "setting sending to %r" % sending

    stop_time = time.clock()

    print 'heartbeat set over %r second(s)' % ((stop_time - start_time))

def transition(illuminators, target, duration):
    start_time = time.clock()

    thresh = 2

    print "changing pair color to %s over %r seconds..." % (target, duration)

    current_time = 0
    previous_time = 0
    delta_time = 0
    for illuminator in illuminators: #TODO define function that checks for distance without having a for loop on 197
        while illuminator.color.distance(target) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.ramp(target, duration, delta_time))

    stop_time = time.clock()
    print "...changed color over %r seconds" % ((stop_time - start_time))


def noise_color(illuminator, color, duration):
    frame_count = 0
    r = color[0]
    g = color[1]
    b = color[2]

    while frame_count < 100:
        #do noise stuff


        frame_count = frame_count + 1
        illuminators[0].set(r, g, b)

    print "done with noise"



#-------------------------LIST USB DEVICES--------------------------------
print "available usb devices:"

illuminators = []

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    # for key in keys:
    #     print "%s : %s" % (key, d[key])
    if d["product_id"] == product_id: # and d["vendor_id"] is vendor_id:
        illuminators.append(Illuminator(d["path"]))

if len(illuminators) > 2 or len(illuminators) == 0:
    print "unexpected amount of light"
    exit(1)

print "succesfully lit illuminator: %r" % illuminators

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
    color = Color(data[0], data[1], data[2])
    duration = data[3]
    transition(illuminators, color, duration)

def handle_color(addr, tags, data, source):
    color = Color(data[0], data[1], data[2])
    for illuminator in illuminators:
        illuminator.set(color)

def handle_heartbeat(addr, tags, data, source):
    heartbeat(data)

def handle_black(addr, tags, data, source):
    illuminator.turn_off()

def handle_noise(addr, tags, data, source):
    noise_color(data)

print "endpoints:"
print "---"
print "/change r g b t ---- changes the color to the specified rgb values over t seconds"
print "/color r g b ---- changes the color immediately"
print "/heartbeat r g b t --- pulsates to the target color over t seconds"
print "/black --- turns off the lamp"
print "/noise --- noise"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/heartbeat', handle_heartbeat)
s.addMsgHandler('/black', handle_black)
s.addMsgHandler('/noise', handle_noise)

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
