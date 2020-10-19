import time
import threading

#_lock = threading.Lock()


def _io_bound():

    while True:
        time.sleep(1)
        print("io: ", threading.current_thread().ident)

        # _lock.acquire()
        # for i in range(10000000):
        #     pass
        # _lock.release()


def _cpu_bound():
    k = 0
    while k < 50:
        for i in range(1000000):
            pass
        #print(threading.current_thread().ident)
        #k += 1
        #print(k)
        # if k == 5:
        #     break
        #k += 1

        #print(k)


import os
import sys
import time
print(sys.executable, " ", os.getpid())
t0 = time.time()
# import gil_load
# gil_load.init()
# gil_load.start(output=sys.stdout)

for i in range(1):
    t = threading.Thread(target=_io_bound)
    t.daemon = True
    t.start()
wait_threads = []
for i in range(3):
    t = threading.Thread(target=_cpu_bound)
    t.daemon = True
    t.start()
    wait_threads.append(t)
print("all threads created!")
# try:
for t in wait_threads:
    t.join()
# except:
#     sys.exit(0)
print("Elapsed=%0.6f" % (time.time() - t0))
