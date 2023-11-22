import typing as t

from matplotlib.figure import Figure
from matplotlib.axes import Axes

from ..typing import SequenceProto


class AxesKwargs(t.TypedDict, total=False):
    xlim: tuple[float, float]
    ylim: tuple[float, float]
    xticks: SequenceProto[float]
    yticks: SequenceProto[float]
    xlabel: str
    ylabel: str
    legend: bool  # default True


def handle_axes_kwargs(axes: Axes, /, **kwargs: t.Unpack[AxesKwargs]):
    if xlim := kwargs.get("xlim"):
        axes.set_xlim(xlim)
    if ylim := kwargs.get("ylim"):
        axes.set_ylim(ylim)
    if xticks := kwargs.get("xticks"):
        axes.set_xticks(xticks)
    if yticks := kwargs.get("yticks"):
        axes.set_yticks(yticks)
    if xlabel := kwargs.get("xlabel"):
        axes.set_xlabel(xlabel)
    if ylabel := kwargs.get("ylabel"):
        axes.set_ylabel(ylabel)
    
    if kwargs.get("legend", True):
        axes.legend()


class FigureKwargs(t.TypedDict, total=False):
    savepath: str


def handle_figure_kwargs(fig: Figure, /, **kwargs: t.Unpack[FigureKwargs]):
    if savepath := kwargs.get("savepath"):
        fig.savefig(savepath)
