# pyright: strict
from typing import (
    Callable, Any, SupportsIndex, Protocol, overload, Sequence, Iterator, 
    Self, Iterable, Sized,
    runtime_checkable
)


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


@runtime_checkable
class SupportsGetItem[T](Protocol):
    def __getitem__(self: Self, __key: SupportsIndex) -> T: ...


@runtime_checkable
class SequenceProto[T](Iterable[T], Sized, SupportsGetItem[T], Protocol):
    """
    __iter__, __len__, and __getitem__ should be present.

    Note that this lacks some methods from collections.abc.Sequence,
    __contains__, __reversed__, index and count.
    """
    pass


@runtime_checkable
class SequenceNotStr[T](Protocol):
    """
    See this thread for information and rationale behind this:
    https://github.com/python/typing/issues/256#issuecomment-1442633430
    """
    @overload
    def __getitem__(self, index: SupportsIndex, /) -> T: ...
    @overload
    def __getitem__(self, index: slice, /) -> Sequence[T]: ...
    # __contains__ in str is incompatible with this
    def __contains__(self, value: object, /) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[T]: ...
    def index(self, value: Any, /, start: int = 0, stop: int = ...) -> int: ...
    def count(self, value: Any, /) -> int: ...
    def __reversed__(self) -> Iterator[T]: ...


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
