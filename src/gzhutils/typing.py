# pyright: strict
import typing as t


def with_signature_of[**P, R](
        func: t.Callable[P, R]
) -> t.Callable[[t.Callable[P, R]], t.Callable[P, R]]:
    return lambda f: f


def with_params_of[**P](ref_func: t.Callable[P, t.Any]):
    def decorate[R](f: t.Callable[P, R]) -> t.Callable[P, R]:
        return f
    return decorate


def typed_args_kwargs[**P](ref_func: t.Callable[P, t.Any]):
    def f(*args: P.args, **kwargs: P.kwargs):
        return args, kwargs
    
    return f


@t.runtime_checkable
class SupportsGetItem[T](t.Protocol):
    def __getitem__(self: t.Self, __key: t.SupportsIndex, /) -> T: ...


@t.runtime_checkable
class SupportsReversed[T](t.Protocol):
    def __reversed__(self: t.Self) -> t.Iterator[T]: ...


@t.runtime_checkable
class SupportsIndexing(t.Protocol):
    """
    Note that this is different from typing.SupportsIndex
    """
    def index(self: t.Self, _1: t.Any, /) -> int:
        ...


@t.runtime_checkable
class SupportsCounting(t.Protocol):
    def count(self: t.Self, __value: t.Any, /) -> int:
        ...


@t.runtime_checkable
class CollectionProto[T](t.Iterable[T], t.Sized, t.Protocol):
    def __contains__(self: t.Self, __key: object, /) -> bool: ...


@t.runtime_checkable
class SequenceProto[T](
        CollectionProto[T], 
        SupportsGetItem[T], 
        SupportsReversed[T],
        SupportsIndexing,
        SupportsCounting,
        t.Protocol
):
    pass


if __name__ == "__main__":
    def f(a: int, b: str) -> float:
        return float(b) + a
    
    @with_params_of(f)
    def g1(*args: t.Any, **kwargs: t.Any):
        return b"133"
    
    a = g1(1, '123')

    @with_signature_of(f)
    def g2(*args: t.Any, **kwrags: t.Any):
        return 123.
    
    b = g2(1, '123')
