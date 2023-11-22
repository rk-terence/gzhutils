import typing as t
from contextlib import contextmanager

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


@t.type_check_only
class VisOptions(t.TypedDict, total=False):
    figsize: tuple[float, float]
    font: str
    fontsize: float
    dpi: int
    tight_layout: bool
    bbox_inches: str
    # scatter plots
    s: float
    # global fig options not controlled by plt.rc_context
    show: bool
    clear: bool


_DEFAULT_OPTIONS: VisOptions = {
    "figsize": (8, 4),
    "font": "Times New Roman",
    "fontsize": 10,  # this is also the default of matplotlib
    "dpi": 600,
    "tight_layout": True,
    "bbox_inches": "tight",
    # Scatter plot
    "s": 3,
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
        assert key in _DEFAULT_OPTIONS, f"Unknown option: {key}"
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
            with _rc_context(**options) as rc:
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
) -> t.Generator[dict[str, t.Any], None, None]:
    options = _DEFAULT_OPTIONS | options | _options
    rc = _vis_options_to_plt_rc_params(**options)
    with plt.rc_context(rc=rc):
        yield rc


@contextmanager
def rc_context(
        **options: t.Unpack[VisOptions]
) -> t.Generator[dict[str, t.Any], None, None]:
    """
    useful when using the matplotlib API directly.
    """
    options = _DEFAULT_OPTIONS | _options | options
    rc = _vis_options_to_plt_rc_params(**options)
    with plt.rc_context(rc=rc):
        yield rc


def _vis_options_to_plt_rc_params(
        **options: t.Unpack[VisOptions]
) -> dict[str, t.Any]:
    rc: dict[str, t.Any] = {}
    for key, value in options.items():
        match key:
            case "figsize":
                rc["figure.figsize"] = value
            case "font":
                rc["font.family"] = value
            case "fontsize":
                rc["font.size"] = value
            case "dpi":
                rc["savefig.dpi"] = value
            case "tight_layout":
                rc["figure.autolayout"] = value
            case "bbox_inches":
                rc["savefig.bbox"] = value
            case "s":
                rc["lines.markersize"] = value
            case "show" | "clear":
                pass
            case _:
                raise ValueError(f"Unknown option: {key}")
    
    return rc
