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

beating = False

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

    def lerp(self, origin, target, duration, lerp_val, delta_time):
        # r = ramp(self.r, color.r, duration, delta_time)
        # b = ramp(self.b, color.b, duration, delta_time)
        # g = ramp(self.g, color.g, duration, delta_time)
        # self.r = self.r + lerp_val*delta_time*duration(color.r-self.r)
        self.r = origin.r + lerp_val*(color.r-origin.r)*delta_time
        self.g = origin.g + lerp_val*(color.g-origin.g)*delta_time
        self.b = origin.b + lerp_val*(color.b-origin.b)*delta_time
        return Color(self.r, self.g, self.b)

    def distance(self, other):
        return max(max(abs(self.r - other.r), abs(self.g - other.g)), abs(self.b - other.b))


BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)



class Illuminator:
    def __init__(self, path):
        self.path = path
        self.color = BLACK
        # self.connection = hid.device(None, None, path)
        # self.connection.set_nonblocking(1)
        self.turn_off()

    def close(self):
        self.connection.close()

    def turn_off(self):
        self.set(Color(0, 0, 0))

    def set(self, color):
        try:
            # data = [0x6, 0x1, color.r, color.g, color.b, 0]
            # checksum = -(twos_comp(sum_data_bytes(data))) % 256
            # message  = [header_byte] + data + [checksum, footer_byte]
            # self.connection.write(message)
            # print "setting color for illuminator to %s" % color
            self.color = color

        except IOError, ex:
            print ex
            self.connection.close()





#-------------------------COLOR METHODS--------------------------------
#heartbeat ramps from the current color to the target color over t seconds, then ramps back down to the starting color
def heartbeat(illuminators, target, duration):
    global beating
    start_time = time.clock()

    previous_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)
    print "previous_color %s" % previous_color

    thresh = 1

    current_time = 0
    previous_time = 0
    delta_time = 0
    lerp_val = 0

    #ramp value up
    for illuminator in illuminators:
        while illuminator.color.distance(target) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.lerp(target, duration, lerp_val, delta_time))
            lerp_val = lerp_val + (0.05/duration)

    lerp_val = 0

    #ramp value down
    for illuminator in illuminators:
        while illuminator.color.distance(previous_color) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.lerp(previous_color, duration, lerp_val, delta_time))
            lerp_val = lerp_val + (0.05/duration)
        beating = False

    stop_time = time.clock()


    print 'heartbeat set over %r second(s) back to %s' % ((stop_time - start_time), previous_color)

def transition(illuminators, target, duration):
    start_time = time.clock()

    lerp_val = 0
    thresh = 2

    print "changing pair color to %s over %r seconds..." % (target, duration)

    current_time = 0
    previous_time = 0
    delta_time = 0
    for illuminator in illuminators:
        while illuminator.color.distance(target) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.lerp(target, duration, lerp_val, delta_time))
            lerp_val = lerp_val + (0.0001 / duration);

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
illuminators.append(Illuminator("lol"))

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    # for key in keys:
    #     print "%s : %s" % (key, d[key])
    # if d["product_id"] == product_id: # and d["vendor_id"] is vendor_id:
        # illuminators.append(Illuminator(d["path"]))

# if len(illuminators) > 2 or len(illuminators) == 0:
#     print "unexpected amount of light"
#     exit(1)
# else:
#     print "succesfully lit illuminator(s): %r" % illuminators


##########################
#	OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)
s.request_queue_size = 1
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
    print "handling change color %s over %r" % (color, duration)
    transition(illuminators, color, duration)

def handle_color(addr, tags, data, source):
    color = Color(data[0], data[1], data[2])
    print "setting color to %s" % color
    for illuminator in illuminators:
        illuminator.set(color)
        illuminator.color = color

def handle_heartbeat(addr, tags, data, source):
    global beating
    color = Color(data[0], data[1], data[2])
    duration = data[3]
    print "received message with beating is %r" % beating
    beating = True
    heartbeat(illuminators, color, duration)

def handle_black(addr, tags, data, source):
    for illuminator in illuminators:
        illuminator.turn_off()


def handle_noise(addr, tags, data, source):
    noise_color(data)

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
s.addMsgHandler('/noise', handle_noise)

#Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
# st = threading.Thread( target = s.serve_forever )
# st.start()
while True:
    if beating is False:
        s.handle_request()

#Threads
try :
	while 1 :
		time.sleep(10)

except KeyboardInterrupt :
    for illuminator in illuminators:
        illuminator.turn_off()
    print "\nClosing OSCServer."
    s.close()
    print "Waiting for Server-thread to finish"
    st.join()
    print "Done"


print "...lights off!"
