import warnings
from typing import Callable, Self
from functools import wraps
from pathlib import Path
from threading import Timer


def deprecated[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def deprecated_func(*args: P.args, **kwargs: P.kwargs) -> R:
        warnings.warn(f"Call to deprecated function {func.__name__}",
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return deprecated_func


def get_project_root() -> Path:
    # this is absolute.
    path = Path.cwd()
    found = False
    while not found:
        iter = filter(
            lambda x: x.name in ('src', '.git'), 
            path.glob('*')
        )
        try:
            next(iter); next(iter)
        except StopIteration:
            path = path.parent
        else:
            found = True
    
    return path


class InfiniteTimer[**P]:
    interval: float
    callback: Callable[P, None]
    timer: Timer | None
    should_stop: bool

    def __init__(
            self: Self, 
            interval: float,
            callback: Callable[P, None],
    ) -> None:
        self.interval = interval
        self.callback = callback

        self.timer = None
        self.should_stop = False

    def function(self: Self, *args: P.args, **kwargs: P.kwargs) -> None:
        self.callback(*args, **kwargs)

        if self.should_stop:
            return
        
        self.timer = Timer(
            interval=self.interval,
            function=self.function,
            args=args,
            kwargs=kwargs
        )
        self.timer.start()


    def run(self: Self, *args: P.args, **kwargs: P.kwargs) -> Self:
        self.timer = Timer(
            interval=self.interval,
            function=self.function,
            args=args,
            kwargs=kwargs
        )
        self.timer.start()

        return self

    def stop(self: Self) -> None:
        if self.timer is None:
            raise RuntimeError("Please run before stop.")
        self.should_stop = True
        self.timer.cancel()
