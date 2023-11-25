# pyright: strict
import inspect
import functools
import typing as t
from collections.abc import Callable, Iterable, Sized, Iterator


def with_signature_of[**P, R](
        func: Callable[P, R]
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    return lambda f: f


def with_params_of[**P](ref_func: Callable[P, t.Any]):
    def decorate[R](f: Callable[P, R]) -> Callable[P, R]:
        return f
    return decorate


def typed_args_kwargs[**P](ref_func: Callable[P, t.Any]):
    def f(*args: P.args, **kwargs: P.kwargs):
        return args, kwargs
    
    return f


def cast[T](type_: type[T], /, obj: object) -> T:
    """
    Compared to the standard lib `typing.cast`, this does more:
    it also tries to cast the runtime object to the specified type.
    """
    return t.cast(T, (t.get_origin(type_) or type_)(obj))


def _naive_is_of_type[T](obj: object, /, type: type[T]) -> t.TypeGuard[T]:
    match anno := t.get_origin(type):
        case None:
            if type is float:
                return isinstance(obj, (int, float))
            else:
                return isinstance(obj, type)
        case t.Literal:
            return obj in t.get_args(type)
        case t.Union:
            return any(_naive_is_of_type(obj, arg) for arg in t.get_args(type))
        case _:
            return isinstance(obj, anno)


def check[T](type_: type[T], /, obj: object) -> T:
    if _naive_is_of_type(obj, type_):
        return obj
    else:
        raise TypeError(f"Expected {obj!r} to be {type_!r}")
    

class Implementation:
    def __init__(self: t.Self, impl: Callable[..., t.Any]) -> None:
        self.impl = impl
        self.signature = inspect.signature(impl)
        
    def visit_params(
            self: t.Self, 
            params_to_check: set[str], 
            diff: dict[str, t.Any]
    ) -> t.Self:
        for name, parameter in self.signature.parameters.items():
            if name not in diff:
                diff[name] = parameter.annotation
            if parameter.annotation != diff[name]:
                params_to_check.add(name)

        return self
    
    def __hash__(self: t.Self) -> int:
        return hash(self.impl)
    
    def __repr__(self: t.Self) -> str:
        return repr(self.signature)
    
    def __call__(self: t.Self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self.impl(*args, **kwargs)


def overload(func: Callable[..., t.Any]) -> Callable[..., t.Any]:
    diff: dict[str, t.Any] = {}
    params_to_check: set[str] = set()
    impls: tuple[Implementation, ...] = tuple(
        Implementation(impl).visit_params(params_to_check, diff) 
        for impl in t.get_overloads(func)
    )

    @functools.cache
    def is_compatible(impl: Implementation, *args: t.Any, **kwargs: t.Any) -> bool:
        try:
            bounded_args = impl.signature.bind(*args, **kwargs)
        except TypeError:
            return False

        for name in params_to_check:
            if name not in bounded_args.arguments:
                continue
            value = bounded_args.arguments[name]
            type_hint = impl.signature.parameters[name].annotation
            parameter = impl.signature.parameters[name]
            if parameter.kind == inspect.Parameter.VAR_POSITIONAL:
                # in wonder if we should take typing.Unpack into account here. 
                # For now, let's say that we ignore it.
                type_hint = tuple[type_hint, ...]
            elif parameter.kind == inspect.Parameter.VAR_KEYWORD:
                if t.get_origin(type_hint) == t.Unpack:
                    type_hint = t.get_args(type_hint)[0]
                else:
                    type_hint = dict[str, type_hint]
            
            if type_hint == inspect.Parameter.empty:
                continue

            if not _naive_is_of_type(value, type_hint):
                return False
        return True

    def func_to_run(*args: t.Any, **kwargs: t.Any) -> t.Any:
        for impl in impls:
            if is_compatible(impl, *args, **kwargs):
                return impl(*args, **kwargs)
        else:
            raise TypeError(f"Cannot find an overload for {func!r}")

    return func_to_run


@t.runtime_checkable
class SupportsGetItem[T](t.Protocol):
    def __getitem__(self: t.Self, __key: t.SupportsIndex, /) -> T: ...


@t.runtime_checkable
class SupportsReversed[T](t.Protocol):
    def __reversed__(self: t.Self) -> Iterator[T]: ...


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
class CollectionProto[T](Iterable[T], Sized, t.Protocol):
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
