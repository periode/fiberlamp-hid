#dependencies:
#pyOSC 0.3.5
import socket, OSC, threading, time

receive_address = ('127.0.0.1', 7000) #Mac Adress, Outgoing Port

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

def handle_color(addr, tags, data, source):
    print "---"
    print "handling color from %s" % OSC.getUrlStr(source)
    print "with addr %s" % addr
    print "tags %s" % tags
    print "data %s" % data
    print "---"

def handle_transition(addr, tags, data, source):
    print "---"
    print "handling transition from %s" % OSC.getUrlStr(source)
    print "with addr %s" % addr
    print "tags %s" % tags
    print "data %s" % data
    print "---"

print "endpoints:"
print "---"
print "/change r g b t"
print "/color r g b:"
print "/transition t"
print "---"

s.addMsgHandler('/', handle_root)
s.addMsgHandler('/change', handle_change)
s.addMsgHandler('/color', handle_color)
s.addMsgHandler('/transition', handle_transition)

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
