#dependencies
# --cython-hid
# --OSC

import hid
import math
import random
import time
from noise import pnoise1
import socket, OSC, threading
import colorsys
import ctypes

#IP Adress and outgoing port to listen on
receive_address = ('0.0.0.0', 7000)

header_byte = 0xa9
footer_byte = 0x5c

#specific to the lamp used
vendor_id = 0x24c2
product_id = 0x1306

#time variables for timed transition
current_time = 0.0
previous_time = 0.0
delta_time = 0.0

color_thread = None
prev_color = None

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


#terminate a thread
def terminate_thread(thread):
    if not thread.isAlive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_long(thread.ident), exc)
    if res == 0:
        raise ValueError("nonexistent thread id")
    elif res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


#check if a thread is still active, then terminate it
def clear_thread():
    global color_thread

    if color_thread is not None:
        terminate_thread(color_thread)
        color_thread = None
        print "first clearing thread..."


#map a value from one range to another
def remap(value, start1, end1, start2, end2):
    start_range = end1 - start1
    end_range = end2 - start2

    value_scaled = float(value - start1)/float(start_range)
    return start2 + value_scaled * end_range


#-------------------------CLASSES--------------------------------
class Color:
    def __init__(self, r, g, b):
        self.r = clamp(r)
        self.g = clamp(g)
        self.b = clamp(b)

    def __str__(self):
        return "color(%i, %i, %i)" % (self.r, self.g, self.b)

    def lerp(self, origin, target, lerp_val):
        self.r = origin.r + lerp_val*(target.r-origin.r)
        self.g = origin.g + lerp_val*(target.g-origin.g)
        self.b = origin.b + lerp_val*(target.b-origin.b)
        return Color(self.r, self.g, self.b)

    def distance(self, other):
        return max(max(abs(self.r - other.r), abs(self.g - other.g)), abs(self.b - other.b))

BLACK = Color(0, 0, 0)
WHITE = Color(255, 255, 255)


class Illuminator:
    def __init__(self, path):
        self.path = path
        self.color = BLACK
        self.blink = 0
        self.connection = hid.device(None, None, path)
        self.connection.set_nonblocking(1)
        self.turn_off()

    def close(self):
        self.connection.close()

    def turn_off(self):
        self.set(Color(0, 0, 0))

    def set(self, color):
        try:
            data = [0x6, 0x1, color.r, color.g, color.b, self.blink]
            checksum = -(twos_comp(sum_data_bytes(data))) % 256
            message  = [header_byte] + data + [checksum, footer_byte]
            self.connection.write(message)
            self.color = color

        except IOError, ex:
            print ex
            self.connection.close()

    def set_blinking(self, color, blink):
        try:
            data = [0x6, 0x1, color.r, color.g, color.b, blink]
            checksum = -(twos_comp(sum_data_bytes(data))) % 256
            message  = [header_byte] + data + [checksum, footer_byte]
            self.connection.write(message)
            self.color = color

        except IOError, ex:
            print ex
            self.connection.close()



#-------------------------COLOR METHODS--------------------------------
#heartbeat ramps from the current color to the target color over t seconds, then ramps back down to the starting color
def heartbeat(illuminators, target, duration):
    start_time = time.clock()
    previous_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)
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

            illuminator.set(illuminator.color.lerp(previous_color, target, lerp_val))
            lerp_val = lerp_val + (0.001/duration)

    lerp_val = 0

    #ramp value down
    for illuminator in illuminators:
        while illuminator.color.distance(previous_color) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.lerp(target, previous_color, lerp_val))
            lerp_val = lerp_val + (0.001/duration)
    print 'heartbeat set over %r second(s) back to %s -- DONE' % ((current_time - start_time), previous_color)


#transition from current color to target color over milliseconds
def transition(illuminators, target, duration):
    start_time = time.clock()

    lerp_val = 0
    thresh = 2
    previous_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)

    print "changing pair color to %s over %r seconds..." % (target, duration)

    current_time = 0
    previous_time = 0
    delta_time = 0
    for illuminator in illuminators: #TODO define function that checks for distance without having a for loop on 198
        while illuminator.color.distance(target) > thresh:
            previous_time = current_time
            current_time = time.clock()
            delta_time = current_time - previous_time

            illuminator.set(illuminator.color.lerp(previous_color, target, lerp_val))
            lerp_val = lerp_val + (0.2 / duration);

    illuminator.set(target)

    print "...changed color over %r seconds -- DONE" % ((current_time - start_time))


#flickers randomly between previous color and given color
def random_flicker(illuminators, color, threshold, start_time, duration):
    base_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)

    while True:
        for illuminator in illuminators:
            if random.random() > threshold:
                illuminator.set(color)
                time.sleep(0.1)
            else:
                illuminator.set(base_color)
                time.sleep(0.05)
        if time.clock() > (start_time + duration*0.000001):
            illuminator.set(color)
            print "done blinking"


#modulates the lightness component of the current color with a noise value
def noise_color(illuminators, step, amplitude):
    base_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)
    temp_color = colorsys.rgb_to_hls(remap(base_color.r, 0, 255, 0, 1), remap(base_color.g, 0, 255, 0, 1), remap(base_color.b, 0, 255, 0, 1))

    while True:
        lightness = min(0.1+temp_color[1]*pnoise1(time.clock()*step)*amplitude*0.1, 1)

        final_color_rgb = colorsys.hls_to_rgb(temp_color[0], lightness, temp_color[2])

        final_color = Color(int(remap(final_color_rgb[0], 0, 1, 0, 255)), int(remap(final_color_rgb[1], 0, 1, 0, 255)), int(remap(final_color_rgb[2], 0, 1, 0, 255)))

        for illuminator in illuminators:
            illuminator.set(final_color)
            
        time.sleep(0.001)

def throb_color(illuminators, step, amplitude):
    base_color = Color(illuminators[0].color.r, illuminators[0].color.g, illuminators[0].color.b)
    temp_color = colorsys.rgb_to_hls(remap(base_color.r, 0, 255, 0, 1), remap(base_color.g, 0, 255, 0, 1), remap(base_color.b, 0, 255, 0, 1))

    while True:
        #TODO have a possibility to set high threshold and low threshold?
        lightness = 0.1+remap(temp_color[1]*math.sin(time.clock()*step)*amplitude, -amplitude, amplitude, 0.1, 0.8)

        final_color_rgb = colorsys.hls_to_rgb(temp_color[0], lightness, temp_color[2])
        final_color = Color(int(remap(final_color_rgb[0], 0, 1, 0, 255)), int(remap(final_color_rgb[1], 0, 1, 0, 255)), int(remap(final_color_rgb[2], 0, 1, 0, 255)))

        for illuminator in illuminators:
            illuminator.set(final_color)

        time.sleep(0.001)



#-------------------------LIST USB DEVICES--------------------------------
illuminators = []
for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    # for key in keys:
    #     print "found: %s : %s" % (key, d[key])
    if d["product_id"] == product_id:
        illuminators.append(Illuminator(d["path"]))

if len(illuminators) > 2 or len(illuminators) == 0:
    print "unexpected amount of light"
    exit(1)
else:
    print "succesfully lit illuminator(s): %r" % illuminators


##########################
#	OSC
##########################

# Initialize the OSC server and the client.
s = OSC.OSCServer(receive_address)
s.request_queue_size = 0
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
    print "handling change color"
    global prev_color
    global color_thread

    clear_thread()

    color = Color(data[0], data[1], data[2])
    duration = data[3]

    prev_color = str(illuminators[0].color)

    if (duration < 10):
        for illuminator in illuminators:
            illuminator.set(color)
    else:
        print "handling change color %s over %rms" % (color, duration)
        color_thread = threading.Thread(target=transition, args=(illuminators, color, duration))
        color_thread.start()

def handle_set_change(addr, tags, data, source):
    print "handling change color"
    global color_thread

    clear_thread()

    first_color = Color(data[0], data[1], data[2])

    for illuminator in illuminators:
        illuminator.set(first_color)

    target_color = Color(data[3], data[4], data[5])
    duration = data[6]

    print "handling set change color %s over %rms" % (target_color, duration)
    color_thread = threading.Thread(target=transition, args=(illuminators, target_color, duration))
    color_thread.start()

def handle_color(addr, tags, data, source):
    print "handling set color..."
    global prev_color

    clear_thread()

    color = Color(data[0], data[1], data[2])
    # if str(color) ==  prev_color:
    #     return

    prev_color = str(color)
    print "...setting color"
    for illuminator in illuminators:
        illuminator.set(color)

def handle_heartbeat(addr, tags, data, source):
    print "handling heartbeat"
    global prev_color
    global color_thread

    color = Color(data[0], data[1], data[2])
    prev_color = str(color)
    duration = data[3]*0.00000001

    clear_thread()

    color_thread = threading.Thread(target=heartbeat, args=(illuminators, color , duration))
    color_thread.start()

def handle_black(addr, tags, data, source):
    print "handling black"

    clear_thread()

    for illuminator in illuminators:
        illuminator.turn_off()


def handle_blink(addr, tags, data, source):
    print "handling blink"
    global color_thread

    clear_thread()

    start_time = time.clock()
    color = Color(data[0], data[1], data[2])
    threshold = data[3]
    duration = data[4]

    color_thread = threading.Thread(target=random_flicker, args=(illuminators, color, threshold, start_time, duration))
    color_thread.start()


def handle_noise(addr, tags, data, source):
    print "handling noise"
    global color_thread

    clear_thread()

    step = data[0]
    amplitude = data[1]

    color_thread = threading.Thread(target=noise_color, args=(illuminators, step, amplitude))
    color_thread.start()

def handle_throb(addr, tags, data, source):
    print "handling throb"
    global color_thread

    clear_thread()

    step = data[0]
    amplitude = data[1]

    color_thread = threading.Thread(target=throb_color, args=(illuminators, step, amplitude))
    color_thread.start()


def handle_throbendo(addr, tags, data, source):
    print "handling throbendo"
    global color_thread

    clear_thread()


def handle_break(addr, tags, data, source):
    print "handling break"
    clear_thread()
    global color_thread
    color_thread = None

#TODO write the /throbendo
print "endpoints:"
print "---"
print "/change r g b t ---- changes the color to the specified rgb values over t ms"
print "/set_change r1 g1 b1 r2 g2 b2 t ---- sets the color to r1 g1 b1 and then changes to r2 g2 b2 over t ms"
print "/color r g b ---- changes the color immediately"
print "/heartbeat r g b t --- pulsates to the target color over t ms"
print "/noise s a --- noise over the lightness component of the previous color with step s (1-10) and amplitude a (1-10)"
print "/throb s a --- sine over the lightness component of the previous color with step s (1-10) and amplitude a (1-10)"
print "/throbendo --- exponential sine over the lightness component of the previous color"
print "/black --- turns off the lamp"
print "/break --- interrupts the current command"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/set_change', handle_set_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/heartbeat', handle_heartbeat)
s.addMsgHandler('/throb', handle_throb);
s.addMsgHandler('/black', handle_black)
s.addMsgHandler('/noise', handle_noise)
s.addMsgHandler('/blink', handle_blink)
s.addMsgHandler('/break', handle_break)

#Start OSCServer
print "\nStarting OSCServer. Use ctrl-C to quit."
st = threading.Thread( target = s.serve_forever )
st.start()
# while True:
#     s.handle_request()

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
