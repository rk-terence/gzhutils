import io
import os
import sys
import ctypes
import tempfile
import warnings
from typing import Callable, Self, Any, Mapping, Literal
from functools import wraps
from pathlib import Path
from threading import main_thread, Thread, Event
from functools import cache
from contextlib import contextmanager


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


def get_all_stdout_redirector(
        sys_name: Literal["Linux", "Windows", "Darwin"]
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
        kernel32 = ctypes.WinDLL('kernel32')
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