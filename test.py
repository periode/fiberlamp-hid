import hid
import time

def twos_comp(val):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (7))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << 8)        # compute negative value
    return val                         # return positive value as is


def tobyte(data):
    result = []
    for b in data:
        result.append(bytes(bytearray([b])))
    return result

def calculate_checksum(message):
    #sum of all bytes
    total = 0
    for byte in message:
        total += byte

    # print "total: %r" % total

    mod = total % 256

    print "final checksum %r" % mod

    return mod

print "-------------------------LIST USB DEVICES--------------------------------"

for d in hid.enumerate(0, 0):
    keys = d.keys()
    keys.sort()
    for key in keys:
        print "%s : %s" % (key, d[key])
    print ""

print "-------------------------PRINT CHECKSUM--------------------------------"

data = [1, 9] #get serial command
print "data: %r" % data
# checksum should be 246 for the get serial command

print "result of two's complement: %r" % twos_comp(246)
checksum = (twos_comp(246) % 256)

print "-------------------------OPEN DEVICE--------------------------------"

try:
    print "Opening device"
    h = hid.device(0x24c2, 0x1306) #vendor_id, product_id, path (optional)
    #h = hid.device(0x1941, 0x8021) # Fine Offset USB Weather Station

    print "Manufacturer: %s" % h.get_manufacturer_string()
    print "Product: %s" % h.get_product_string()
    print "Serial No: %s" % h.get_serial_number_string()

    # try non-blocking mode by uncommenting the next line
    #h.set_nonblocking(1)

    # try writing some data to the device
    # for k in range(10):
    #     for i in [0, 1]:
    #         for j in [0, 1]:
    #             h.write([0x80, i, j])
    #             d = h.read(5)
    #             if d:
    #                 print d
    #             time.sleep(0.05)
    
    data = [1, 9] #get serial command
    print "data: %r" % data
    checksum = 246

    print twos_comp(246)
    
    message = [169] + data + [checksum, 92]

    while True:
        h.write(message)
            d = h.read(255)
        print d
        print "received byte: %r" % bytes(bytearray(d))

    print "Closing device"
    h.close()

except IOError, ex:
    print ex
    print "You probably don't have the hard coded test hid. Update the hid.device line"
    print "in this script with one from the enumeration list output above and try again."

print "Done"





