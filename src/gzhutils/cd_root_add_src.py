"""
NOTE: importing this module will cause the change of current directory
and python search path.

USE WITH CARE.

The current working directory will be changed to the closest 
parent directory that contains both "src" and ".git" entries. 
I assume the folder with such entries to be the root directory
of your project.

The python search path (`sys.path`) will be modified. 
Specifically, the src directory will be added to it if it is not in yet.
"""
import os
import sys
from pathlib import Path
import logging

from .miscellaneous import get_project_root


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
    logger.warning(f'CWD Before changing: {Path.cwd()}')
    proot = get_project_root()
    os.chdir(proot)
    logger.warning(f'CWD After changing: {proot}')

    return proot


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
    logger.warning(f'Appended {src} to sys.path')


append_src_to_path(cd_project_root())
