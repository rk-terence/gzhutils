# verify the installation of optional dependencies for VIS
try:
    import matplotlib as _
    import numpy as _
except ModuleNotFoundError:
    # By explicitly setting the __cause__ of the exception to None,
    # the __suppress_context__ attribute of the exception will be set to True.
    # So although the default value of __cause__ is None, we still need to 
    # explicitly set it to None to avoid the 
    # "during handling..." traceback message.
    # See https://stackoverflow.com/a/24752607/13285709 for more details.
    raise ModuleNotFoundError(
        "matplotlib and numpy are required for visualization. "
        "Try `pip install gzhutils[vis]`, which will include the dependencies "
        "needed by visualization."
    ) from None

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
