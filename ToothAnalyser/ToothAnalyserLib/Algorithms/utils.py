"""
ToothAnalyserLib.Algorithm.utils
=================================

This module provides general standard functions and decorators that may be useful for all algorithms.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.


Author
-------
Lukas Konietzka, lukas.konietzka@tha.de
"""



def measure_time(func):
    """
    This function is a decorator to measure the
    runtime of a method
    @param func:
    @return:
    """
    import time
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        stop = time.time()

        elapsed = stop - start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        print(f"{func.__name__}: Done {minutes}:{seconds:02d} minutes")
        return result

    return wrapper