# pyright: strict
from typing import Callable, Any


def with_signature_of[**P, R](
        func: Callable[P, R]
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return lambda f: f


def with_params_of[**P](func: Callable[P, Any]):
    def decorate[R](f: Callable[P, R]) -> Callable[P, R]:
        return f
    return decorate


def typed_args_kwargs[**P](func: Callable[P, Any]):
    def f(*args: P.args, **kwargs: P.kwargs):
        return args, kwargs
    
    return f


if __name__ == "__main__":
    def f(a: int, b: str) -> float:
        return float(b) + a
    
    @with_params_of(f)
    def g1(*args: Any, **kwargs: Any):
        return b"133"
    
    a = g1(1, '123')

    @with_signature_of(f)
    def g2(*args: Any, **kwrags: Any):
        return 123.
    
    b = g2(1, '123')
