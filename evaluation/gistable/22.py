"""time.process_time() and time.perf_counter() for Python 2 on Ubuntu."""
import ctypes
import errno
from ctypes.util import find_library
from functools import partial

CLOCK_PROCESS_CPUTIME_ID = 2  # time.h
CLOCK_MONOTONIC_RAW = 4

clockid_t = ctypes.c_int
time_t = ctypes.c_long


class timespec(ctypes.Structure):
    _fields_ = [
        ('tv_sec', time_t),         # seconds
        ('tv_nsec', ctypes.c_long)  # nanoseconds
    ]
_clock_gettime = ctypes.CDLL(find_library('rt'), use_errno=True).clock_gettime
_clock_gettime.argtypes = [clockid_t, ctypes.POINTER(timespec)]


def clock_gettime(clk_id):
    tp = timespec()
    if _clock_gettime(clk_id, ctypes.byref(tp)) < 0:
        err = ctypes.get_errno()
        msg = errno.errorcode[err]
        if err == errno.EINVAL:
            msg += (" The clk_id specified is not supported on this system"
                    " clk_id=%r") % (clk_id,)
        raise OSError(err, msg)
    return tp.tv_sec + tp.tv_nsec * 1e-9

try:
    from time import perf_counter, process_time
except ImportError:  # Python <3.3
    perf_counter = partial(clock_gettime, CLOCK_MONOTONIC_RAW)
    perf_counter.__name__ = 'perf_counter'
    process_time = partial(clock_gettime, CLOCK_PROCESS_CPUTIME_ID)
    process_time.__name__ = 'process_time'

if __name__ == "__main__":
    import random
    import time
    from itertools import repeat
    from timeit import Timer, default_timer

    print("process_time() doesn't include time.sleep(0.5):")
    timers = [default_timer, time.clock, process_time, perf_counter]
    start_times = [t() for t in timers]
    time.sleep(0.5)
    _ = sum(random.random() - f for f in repeat(.5, 1000000))
    for start, timer in zip(start_times, timers):
        print("\t%-12s %.3g" % (timer.__name__, timer() - start))

    # measure overhead
    print("overhead (execute `pass` statement):")
    n = 10000000
    for timer in timers:
        t = min(Timer(timer=timer).repeat(number=n)) / n
        print("\t%-12s  %.2f ns" % (timer.__name__, t*1e9))
