import shutil
from pathlib import Path

from .miscellaneous import get_project_root


type PathLike = Path | str


def clear_dir(path: PathLike) -> None:
    if not (dir := Path(path)).is_absolute():
        dir = get_project_root() / dir
    assert dir.is_dir()
    for entry in dir.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()
