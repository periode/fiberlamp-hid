import socket
import struct
import binascii

UDP_IP = "127.0.0.1"
UDP_PORT = 2046
PACKET_SIZE = 1024

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
print "listening on host %s : %i" % (UDP_IP, UDP_PORT)

while True:
	data, address = sock.recvfrom(PACKET_SIZE)

	print "data received of type %r and length %r" % (type(data), len(data))
	print "data: %r" % data

	hexval = binascii.hexlify(data)
	print "hex value: %r" % hexval
	print "hex value as list: %r" % [hexval[i:i+2] for i in range(0, len(hexval), 2)]

	# unpacked_data = struct.unpack('IIII', data)
	# print type(unpacked_data)
	# # print "unpacked 19: %r" % ''.join(chr(int(x)) for x in unpacked_data[19])
	# for d in unpacked_data:
	# 	print "single data packets %s" % d
