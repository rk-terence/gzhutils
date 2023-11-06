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
        callback=callback
    ).run(1, 2)

    time.sleep(1.09)
    inf_timer.stop()
    
    assert count == 1023
