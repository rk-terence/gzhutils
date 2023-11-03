def printf(string: str) -> None: 
    """
    like `printf` in C, but limited in functionality, i.e., it just prints
    the given string, without formatted print.

    This function uses `printf` in C directly, whose output cannot be 
    redirected by changing `sys.stdout` or by using 
    `contextlib.redirect_stdout`.
    """
    ...
