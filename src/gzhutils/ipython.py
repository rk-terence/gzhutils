from typing import Self


class String(str):
    """
    Pretty print the a given string.
    """
    def _repr_html_(self: Self) -> str:
        return ''.join(
            '<p>' + line + '</p>' for line in self.splitlines()
        )
