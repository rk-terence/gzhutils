import io
import os
import sys
import ctypes
import tempfile
import warnings
import typing as t
from functools import wraps
from pathlib import Path
from threading import Thread, Event
from functools import cache
from contextlib import contextmanager


def deprecated[**P, R](func: t.Callable[P, R]) -> t.Callable[P, R]:
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
            self: t.Self, 
            interval: float,
            callback: t.Callable[P, None]
    ) -> None:
        """
        Please call `setargs` to set args and kwargs of the callback before 
        calling `start` of this thread.
        """
        super().__init__()
        self.interval = interval
        self.callback = callback

        self._should_stop = Event()

    def run(self: t.Self) -> None:
        while True:
            self.callback(*self._args, **self._kwargs)
            if self._should_stop.wait(timeout=self.interval):
                break
    
    def setargs(self: t.Self, *args: P.args, **kwargs: P.kwargs) -> t.Self:
        self._args = args
        self._kwargs = kwargs

        return self

    def stop(self: t.Self) -> None:
        self._should_stop.set()


def get_all_stdout_redirector(
        sys_name: t.Literal["Linux", "Windows", "Darwin"]
):
    """ 
    Copied and modified from 
    https://gist.github.com/natedileas/8eb31dc03b76183c0211cdde57791005

    Capture and redirect stdout which arises from c extension or shared library.

    KNOWN LIMITATIONS: If code block to be executed inside this context manager 
    keeps a reference to the `sys.stdout` and tries to write to it
    (for example, a logger whose handlers already include one sys.stdout
    StreamHandler trying to log message in it), an OSError of invalid handle
    will occur.
    
    More references:
    1. wurlitzer: https://github.com/minrk/wurlitzer
    2. https://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/
    3. https://stackoverflow.com/questions/17942874/stdout-redirection-with-ctypes
    """ 
    if sys_name == "Windows":
        if hasattr(sys, 'gettotalrefcount'): # debug build
            libc = ctypes.CDLL('ucrtbased')
        else:
            libc = ctypes.CDLL('api-ms-win-crt-stdio-l1-1-0')
        # c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
        kernel32 = ctypes.WinDLL('kernel32')  # type: ignore
        STD_OUTPUT_HANDLE = -11
        c_stdout = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    elif sys_name == "Linux":
        libc = ctypes.CDLL(None)  # "libc.so.6"
        c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
    elif sys_name == "Darwin":
        libc = ctypes.CDLL(None)
        c_stdout = ctypes.c_void_p.in_dll(libc, '__stdoutp')

            
    ##############################################################

    @contextmanager
    def all_stdout_redirector(stream: io.BytesIO):
        # use sys.__stdout__ because sys.stdout might be modified by ipython
        # or jupyter, while C prints to the sys.__stdout__.
        c_stdout_fd = sys.__stdout__.fileno()
        stdout_bak = sys.stdout

        def redirect_all_stdout(to_fd: int):
            """Redirect stdout to the given file descriptor."""
            # Flush the C-level buffer stdout
            if sys_name == "Windows":
                libc.fflush(None)   #### CHANGED THIS ARG TO NONE #############
            else:
                libc.fflush(c_stdout)

            # Make c_stdout_fd point to to_fd
            os.dup2(to_fd, c_stdout_fd)

        # Save a copy of the original c_stdout_fd
        saved_c_stdout_fd = os.dup(c_stdout_fd)
        try:
            # Create a temporary file and redirect c extension's stdout to it
            tfile = tempfile.TemporaryFile(mode='w+b')
            sys.stdout = (sio := io.StringIO())
            redirect_all_stdout(tfile.fileno())
            try:
                yield
            finally:
                redirect_all_stdout(saved_c_stdout_fd)
                sys.stdout = stdout_bak
            tfile.flush()
            tfile.seek(0, io.SEEK_SET)
            stream.write(tfile.read())
            stream.write(bytes(sio.getvalue(), encoding='utf-8'))
        finally:
            tfile.close()
            os.close(saved_c_stdout_fd)
    
    return all_stdout_redirector


def postprocessing_decorator_factory[**P, R1, R2](
        post_func: t.Callable[[R1], R2]
) -> t.Callable[[t.Callable[P, R1]], t.Callable[P, R2]]:
    def decorator(
            func: t.Callable[P, R1]
    ) -> t.Callable[P, R2]:
        def func_with_postprocessing(
                *args: P.args,
                **kwargs: P.kwargs
        ) -> R2:
            ret = func(*args, **kwargs)
            return post_func(ret)
        
        return func_with_postprocessing
    
    return decorator


def cascade_decorators[**inP1, inR1, **outP1, outR1, **outP2, outR2](
        decorator_1: t.Callable[[t.Callable[inP1, inR1]], 
                                 t.Callable[outP1, outR1]],
        decorator_2: t.Callable[[t.Callable[outP1, outR1]], 
                                 t.Callable[outP2, outR2]],
) -> t.Callable[[t.Callable[inP1, inR1]], t.Callable[outP2, outR2]]:
    def decorator(
            func: t.Callable[inP1, inR1]
    ) -> t.Callable[outP2, outR2]:
        return decorator_2(decorator_1(func))
    
    return decorator
