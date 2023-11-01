"""
NOTE: importing this module will cause the change of current directory
and python search path.
USE WITH CARE.
"""
import os
import sys
from pathlib import Path
import logging


logger = logging.getLogger(__name__)


def cd_project_root() -> Path:
    """
    Change the current working directory to the project root.
    This is accomplished through repeatedly running
    ```
    cd ..
    ```
    until we have found the root directory of current project.

    What identifies a project root? We are looking for the below two entries:
    - src/
    - .git/

    If both are present, then we assume that this is the project root.

    This utility function is useful when we are running a jupyter notebook
    in JupyterLab and we expect the current working directory to be the 
    project root.
    """
    # this is absolute.
    cwd = Path.cwd()
    logger.info(f'CWD Before changing: {cwd}')
    found = False
    while not found:
        iter = filter(
            lambda x: x.name in ('src', '.git'), 
            cwd.glob('*')
        )
        try:
            next(iter); next(iter)
        except StopIteration:
            cwd = cwd.parent
        else:
            found = True

    os.chdir(cwd)
    logger.info(f'CWD After changing: {cwd}')

    return cwd


def append_src_to_path(root: Path):
    """
    Only append ./src folder to the python search path if it is not in.
    """
    src = root / 'src'
    for p in sys.path:
        path = Path(p).resolve()
        if src == path:
            logger.info(f'{src} directory has already been in sys.path')
            return
    
    sys.path.append(str(src))
    logger.info(f'Appended {src} to sys.path')


append_src_to_path(cd_project_root())
