import warnings
from typing import Callable, Self, Any, Mapping
from functools import wraps
from pathlib import Path
from threading import main_thread, Thread, Event
from functools import cache


def deprecated[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def deprecated_func(*args: P.args, **kwargs: P.kwargs) -> R:
        warnings.warn(f"Call to deprecated function {func.__name__}",
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return deprecated_func


@cache
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


class InfiniteTimer[**P](Thread):
    def __init__(
            self: Self, 
            interval: float,
            callback: Callable[P, None]
    ) -> None:
        """
        Please call `setargs` to set args and kwargs of the callback before 
        calling `start` of this thread.
        """
        super().__init__()
        self.interval = interval
        self.callback = callback

        self._should_stop = Event()

    def run(self: Self) -> None:
        while True:
            self.callback(*self._args, **self._kwargs)
            if self._should_stop.wait(timeout=self.interval):
                break
    
    def setargs(self: Self, *args: P.args, **kwargs: P.kwargs) -> Self:
        self._args = args
        self._kwargs = kwargs

        return self

    def stop(self: Self) -> None:
        self._should_stop.set()
