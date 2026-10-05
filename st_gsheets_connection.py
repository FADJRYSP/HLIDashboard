"""
Local stub for `st_gsheets_connection` to satisfy editor/Pylance when
the real package isn't installed.

This minimal stub provides a `GSheetsConnection` class with a `read`
method that returns an empty DataFrame. Replace with the real
implementation if you install the official package.
"""
from typing import Any
import pandas as pd


class GSheetsConnection:
    """Minimal stub used only to satisfy imports and avoid editor warnings."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def read(self, worksheet: str, ttl: int = 0) -> pd.DataFrame:
        # Return an empty DataFrame so calling code can continue to run
        # without the real Google Sheets connection during editing.
        return pd.DataFrame()


__all__ = ["GSheetsConnection"]
