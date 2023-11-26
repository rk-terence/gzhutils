import shutil
import functools
from pathlib import Path


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


@functools.cache
def get_project_root() -> Path:
    # this is absolute.
    path = Path.cwd()
    found = False
    while not found:
        iter = filter(
            lambda x: x.name in ('src', '.git'), 
            path.glob('*')
        )
        try:
            next(iter); next(iter)
        except StopIteration:
            path = path.parent
        else:
            found = True
    
    return path
