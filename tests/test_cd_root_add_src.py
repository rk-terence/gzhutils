import os
import sys
from itertools import pairwise
from pathlib import Path
import importlib


os.chdir('./src/gzhutils/')
import gzhutils.cd_root_add_src


def test_cd_root():
    cwd = Path.cwd()
    assert cwd.name == 'gzhutils'
    assert 'pyproject.toml' in tuple(path.name for path in cwd.glob('*'))


def test_add_src():
    found = False
    src = Path.cwd() / 'src'
    for p1, p2 in pairwise(Path(p) for p in sys.path):
        assert p1 != p2
        if p1 == src or p2 == src:
            found = True
    assert found


def test_reload():
    importlib.reload(gzhutils.cd_root_add_src)
    test_cd_root()
    test_add_src()

    print(sys.path)
    print(Path.cwd())
