import time


start_r = 0
start_g = 0
start_b = 0

current_time = 0.0
previous_time = 0.0
delta_time = 0.0

def transition(target_r, target_g, target_b, t):
    global start_r
    global start_g
    global start_b

    global current_time
    global previous_time
    global delta_time
    
    start_time = time.clock()

    while start_r < target_r:
        previous_time = current_time
        current_time = time.clock()
        delta_time = current_time - previous_time
        # print 'delta_time: %r' % delta_time
        start_r = start_r + ((delta_time*target_r)/t)
        start_g = start_g + ((delta_time*target_g)/t)
        start_b = start_b + ((delta_time*target_b)/t)

    stop_time = time.clock()
    print 'completed in %r' % (stop_time - start_time)
    print 'values on end: r %r g %r b %r' % (start_r, start_g, start_b)


transition(200, 100, 40, 2)
