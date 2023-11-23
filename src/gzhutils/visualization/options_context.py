import logging
import typing as t
from contextlib import contextmanager

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


logger = logging.getLogger(__name__)


class VisOptions(t.TypedDict, total=False):
    figsize: tuple[float, float]
    figratio: float
    font: str
    fontsize: float  # matplotlib default is 10 (pt)
    dpi: int  # fig dpi, matplotlib default is 100
    savedpi: int  # save.dpi, matplotlib default is figure.dpi
    tight_layout: bool
    bbox_inches: t.Literal["tight", "standard"]
    # math
    mathfont: t.Literal["dejavusans", "dejavuserif", "stix", "stixsans", "cm"]
    # plot
    linewidth: float
    markersize: float  # s in scatter is by default markersize ** 2
    # global fig options not controlled by plt.rc_context
    show: bool
    clear: bool


_DEFAULT_OPTIONS: VisOptions = {
    "figratio": 2,
    "font": "Times New Roman",
    "fontsize": 10,  # this is also the default of matplotlib
    "tight_layout": True,
    "dpi": 100,
    "savedpi": 600,
    "bbox_inches": "tight",
    "mathfont": "cm",
    # plot
    "linewidth": 2,
    "markersize": 6,
    # my options
    "show": True,
    "clear": True
}

# The global options used for all visualizations.
# If specified, will override the corresponding default options.
_options: VisOptions = {}

# prop_cycle = plt.rcParams["axes.prop_cycle"]
# DEFAULT_COLORS: list = prop_cycle.by_key()["color"]


def set_options(**options: t.Unpack[VisOptions]):
    for key, value in options.items():
        assert key in VisOptions.__optional_keys__, f"Unknown option: {key}"
        _options[key] = value


class VisOptionsContext:
    """
    Use this context manager if you wnat to temporarily change the options.
    Note that only drawing functions in this package, or functions decorated 
    by `run_with_context` are affected.
    """
    def __init__(self, **options: t.Unpack[VisOptions]):
        self.options = options
        self._options_bak = _options
    
    def __enter__(self):
        global _options
        _options = _options | self.options
    
    def __exit__(self, *args):
        global _options
        _options = self._options_bak


@t.overload
def run_with_context[**P](
        func: None = None,
        **options: t.Unpack[VisOptions]
) -> t.Callable[[t.Callable[P, Figure]], t.Callable[P, Figure]]:
    ...
@t.overload
def run_with_context[**P](
        func: t.Callable[P, Figure],
        **options: t.Unpack[VisOptions]
) -> t.Callable[P, Figure]:
    ...
def run_with_context[**P](
        func: t.Callable[P, Figure] | None = None, 
        **options: t.Unpack[VisOptions]
) -> (
        t.Callable[P, Figure] 
        | t.Callable[[t.Callable[P, Figure]], t.Callable[P, Figure]]
):
    def wrap(func: t.Callable[P, Figure]) -> t.Callable[P, Figure]:
        def func_with_context(*args: P.args, **kwargs: P.kwargs) -> Figure:
            with _rc_context(**options) as (_, rc):
                fig = func(*args, **kwargs)
                if rc.get("show", True):
                    plt.show()
                if rc.get("clear", True):
                    fig.clear()
            return fig
        return func_with_context
    
    if func is None:
        return wrap
    else:
        return wrap(func)
    

@contextmanager
def _rc_context(
        **options: t.Unpack[VisOptions]
) -> t.Generator[tuple[dict[str, t.Any], VisOptions], None, None]:
    options = _DEFAULT_OPTIONS | options | _options
    mpl_rc, rc = _vis_options_to_rc_params(**options)
    with plt.rc_context(rc=mpl_rc):
        yield mpl_rc, rc


@contextmanager
def rc_context(
        **options: t.Unpack[VisOptions]
) -> t.Generator[dict[str, t.Any], None, None]:
    """
    useful when using the matplotlib API directly.
    """
    options = _DEFAULT_OPTIONS | _options | options
    mpl_rc, _ = _vis_options_to_rc_params(**options)
    with plt.rc_context(rc=mpl_rc):
        yield mpl_rc


def _vis_options_to_rc_params(
        **options: t.Unpack[VisOptions]
) -> tuple[dict[str, t.Any], VisOptions]:
    mpl_rc: dict[str, t.Any] = {}
    rc: VisOptions = {}
    for key, value in options.items():
        match key:
            case "figsize":
                mpl_rc["figure.figsize"] = value
                logger.warning(
                    "Option 'figsize' is deprecated and preceded by "
                    "'figratio'. Consider use 'figratio' instead.")
            case "figratio":
                w, h = 6.4, 6.4 / t.cast(float, value)
                mpl_rc["figure.figsize"] = (w, h)
            case "font":
                mpl_rc["font.family"] = value
            case "fontsize":
                mpl_rc["font.size"] = value
            case "dpi":
                mpl_rc["figure.dpi"] = value
            case "savedpi":
                mpl_rc["savefig.dpi"] = value
            case "tight_layout":
                mpl_rc["figure.autolayout"] = value
            case "bbox_inches":
                mpl_rc["savefig.bbox"] = value
            case "mathfont":
                mpl_rc["mathtext.fontset"] = value
            case "linewidth":
                mpl_rc["lines.linewidth"] = value
            case "markersize":
                mpl_rc["lines.markersize"] = value
            case "show" | "clear":
                # These are not matplotlib rc params,
                # and processed in `run_with_context`.
                rc[key] = t.cast(t.Any, value)
            case _:
                raise ValueError(f"Unknown option: {key}")
    
    return mpl_rc, rc
