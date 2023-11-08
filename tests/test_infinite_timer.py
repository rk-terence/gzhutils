import time

from gzhutils.miscellaneous import InfiniteTimer


def test_infinite_timer():
    count = 0

    def callback(n: int, k: int = 2):
        nonlocal count
        count = k * count + n
        print(count)

    inf_timer = InfiniteTimer(
        interval=0.1,
        callback=callback,
    ).setargs(1, 2)
    inf_timer.start()

    time.sleep(0.99)
    inf_timer.stop()
    
    assert count == 1023
