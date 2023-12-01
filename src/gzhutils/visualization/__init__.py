# verify the installation of optional dependencies for VIS
try:
    import matplotlib as _
    import numpy as _
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "matplotlib and numpy are required for visualization. "
        "Try `pip install gzhutils[vis]`, which will include the dependencies "
        "needed by visualization."
    )

from .draw_funcs import (
    plot_one, plot_multiple, plot_consecutive,
    scatter_one, scatter_multiple, scatter_consecutive,
    parity_plot
)
from .options_context import (
    VisOptions, VisOptionsContext, set_options, rc_context
)
from .utils import AxesKwargs, FigureKwargs


__all__ = [
    "plot_one", "plot_multiple", "plot_consecutive",
    "scatter_one", "scatter_multiple", "scatter_consecutive",
    "parity_plot",
    "VisOptionsContext", "set_options", "rc_context",
    "VisOptions", "AxesKwargs", "FigureKwargs"
]
