import hid
import time

header_byte = 0xa9
footer_byte = 0x5c

vendor_id = 0x24c2
product_id = 0x1306

def twos_comp(val):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (7))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << 8)        # compute negative value
    return val                         # return positive value as is

#calculate the sum, 

def tobyte(data):
    result = []
    for b in data:
        result.append(bytes(bytearray([b])))
    return result

def sum_data_bytes(message):
    total = sum(message)
    mod = total % 256

    return mod

print "-------------------------LIST USB DEVICES--------------------------------"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""

print "-------------------------PRINT CHECKSUM--------------------------------"

data = [0x6, 0x1, 0x49, 0x02, 0x8b, 0x00] #command
print "sum of bytes: %r" % sum_data_bytes(data)
print "result of two's complement: %r" % twos_comp(sum_data_bytes(data))

checksum = (twos_comp(sum_data_bytes(data)) % 256)
print "checksum: %r" % checksum

print "-------------------------OPEN DEVICE--------------------------------"

try:
    print "Opening device"
    h = hid.device(vendor_id, product_id)

    print "Manufacturer: %r" % h.get_manufacturer_string()
    print "Product: %r" % h.get_product_string()
    print "Serial No: %r" % h.get_serial_number_string()

    # try non-blocking mode by uncommenting the next line
    #h.set_nonblocking(1)
    
    #whole message: header + length + command + optional data payload + checksum + cookie
    message = [header_byte] + data + [0x23, footer_byte]

    while True:
        h.write(message)
        print "message sent: %r" % message
        d = h.read(255)
        print "received byte: %r\n" % bytes(bytearray(d))

    print "Closing device"
    h.close()

except IOError, ex:
    print ex
    print "You probably don't have the hard coded test hid. Update the hid.device line"
    print "in this script with one from the enumeration list output above and try again."

print "Done"





