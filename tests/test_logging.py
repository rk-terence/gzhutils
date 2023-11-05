import io
import os

from gzhutils.logging import redirect_all_stdout
from gzhutils import printf


def test_redirector():
    f = io.StringIO()
    echo_text = "This is from echo"
    printf_text = "This is from printf"
    with redirect_all_stdout(f):
        printf(printf_text)
        os.system("echo " + '"' + echo_text + '"')
    print(f.getvalue())
    assert all(text in f.getvalue() for text in (echo_text, printf_text))
