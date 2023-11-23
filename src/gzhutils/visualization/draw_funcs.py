from functools import partial
import typing as t

import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from .options_context import run_with_context
from . import utils as u
from ..typing import SequenceProto, CollectionProto, with_signature_of


# constrained type specifications cannot be used here, 
# see https://github.com/microsoft/pyright/issues/6521
type Array = SequenceProto[np.generic] | SequenceProto[float] | NDArray[t.Any]


class _GeneralKwargs(u.AxesKwargs, u.FigureKwargs):
    pass


class DrawFuncAtom(t.Protocol):
    def __call__(
            self: t.Self,
            axes: Axes,
            y: Array,
            label: str,
            fmt: str | None = None,
            x: Array | None = None
    ) -> None:
        ...


def _plot(
        axes: Axes,
        y: Array,
        label: str,
        fmt: str | None = None,
        x: Array | None = None
) -> None:
    if fmt:
        if x is None:
            axes.plot(y, fmt, label=label)
        else:
            axes.plot(x, y, fmt, label=label)
    else:
        if x is None:
            axes.plot(y, label=label)
        else:
            axes.plot(x, y, label=label)


def _scatter(
        axes: Axes,
        y: Array,
        label: str,
        fmt: str | None = None,
        x: Array | None = None
) -> None:
    if x is None:
        axes.scatter(range(len(y)), y, label=label)
    else:
        axes.scatter(x, y, label=label)


@run_with_context
def _draw_one(
        draw: DrawFuncAtom,
        y: Array,
        label: str,
        fmt: str | None = None,
        **kwargs: t.Unpack[_GeneralKwargs]
) -> Figure:
    fig = plt.figure()
    axes = fig.add_subplot()
    draw(axes, y, label, fmt)
    u.handle_axes_kwargs(axes, **kwargs)
    u.handle_figure_kwargs(fig, **kwargs)
    return fig


@with_signature_of(__plot_one := partial(_draw_one, _plot))
def plot_one(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __plot_one(*args, **kwargs)


@with_signature_of(__scatter_one := partial(_draw_one, _scatter))
def scatter_one(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __scatter_one(*args, **kwargs)


@run_with_context
def _draw_multiple(
        draw: DrawFuncAtom,
        ys: CollectionProto[Array],
        labels: CollectionProto[str],
        fmts: CollectionProto[str] | None = None,
        subplots: bool = False,
        **kwargs: t.Unpack[_GeneralKwargs]
) -> Figure:
    if fmts is None: 
        fmts_ = (None for _ in range(len(ys)))
    else:
        fmts_ = fmts

    fig = plt.figure()
    if subplots:
        n_cols = kwargs.get("n_cols", 1)
        n_rows = (len(ys) + n_cols - 1) // n_cols
        for i, (y, label, fmt) in enumerate(zip(ys, labels, fmts_)):
            axes = fig.add_subplot(n_rows, n_cols, i + 1)
            draw(axes, y, label, fmt)
            u.handle_axes_kwargs(axes, **kwargs)
    else:
        axes = fig.add_subplot()
        for y, label, fmt in zip(ys, labels, fmts_):
            draw(axes, y, label, fmt)
        u.handle_axes_kwargs(axes, **kwargs)
    u.handle_figure_kwargs(fig, **kwargs)

    return fig


@with_signature_of(__plot_multiple := partial(_draw_multiple, _plot))
def plot_multiple(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __plot_multiple(*args, **kwargs)


@with_signature_of(__scatter_multiple := partial(_draw_multiple, _scatter))
def scatter_multiple(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __scatter_multiple(*args, **kwargs)


@run_with_context
def _draw_consecutive(
        draw: DrawFuncAtom,
        ys: CollectionProto[Array],
        labels: CollectionProto[str],
        fmt: str | None = None,
        **kwargs: t.Unpack[_GeneralKwargs]
) -> Figure:
    fig = plt.figure()
    axes = fig.add_subplot()
    start = 0
    for y, label in zip(ys, labels):
        end = start + len(y)
        draw(axes, y, label, fmt, x=range(start, end))
        start = end

    u.handle_axes_kwargs(axes, **kwargs)
    u.handle_figure_kwargs(fig, **kwargs)

    return fig


@with_signature_of(__plot_consecutive := partial(_draw_consecutive, _plot))
def plot_consecutive(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __plot_consecutive(*args, **kwargs)


@with_signature_of(__scatter_consecutive 
                   := partial(_draw_consecutive, _scatter))
def scatter_consecutive(*args: t.Any, **kwargs: t.Any) -> t.Any:
    __scatter_consecutive(*args, **kwargs)


@run_with_context(figratio=1)
def parity_plot(
        y_test: Array,
        y_preds: CollectionProto[Array],
        labels: CollectionProto[str],
        **kwargs: t.Unpack[_GeneralKwargs]
) -> Figure:
    assert len(y_preds) == len(labels)

    fig = plt.figure()
    axes = fig.add_subplot()
    axes.set_aspect("equal")
    for y_pred, label in zip(y_preds, labels):
        axes.scatter(y_test, y_pred, label=label)

    # Add a line y=x, and adjust xlim and ylim such that y=x
    # will cross the bottom-left and top-right corner.
    low = np.min(y_test)
    high = np.max(y_test)
    l = low - (high - low) * 0.05
    h = high + (high - low) * 0.05
    axes.set_xlim(l, h)
    axes.set_ylim(l, h)
    axes.plot([l, h], [l, h], linestyle='-.', color='gray')

    axes.set_xlabel('True value')
    axes.set_ylabel('Predicted value')
    axes.legend()

    u.handle_axes_kwargs(axes, **kwargs)
    u.handle_figure_kwargs(fig, **kwargs)
    return fig
