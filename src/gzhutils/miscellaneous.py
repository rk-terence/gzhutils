import warnings
from typing import Callable
from functools import wraps


def deprecated[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def deprecated_func(*args: P.args, **kwargs: P.kwargs) -> R:
        warnings.warn(f"Call to deprecated function {func.__name__}",
                      category=DeprecationWarning,
                      stacklevel=2)
        return func(*args, **kwargs)
    return deprecated_func
