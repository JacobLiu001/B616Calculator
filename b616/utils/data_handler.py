import pandas as pd
from functools import cache
from b616.utils.arcaea_ptt import get_ptt_delta


class DataHandler:
    """A class to handle Arcaea score data.

    Note that the data is immutable after initialization.
    If you want to modify the data, you should create a new DataHandler object.
    This enables caching of some computationally expensive methods.

    The data returned is sorted by PTT in descending order.

    NOTE: All returned data are copies of the original data, so they are safe to modify.
    Using Copy-On-Write mode in pandas is strongly recommended for performance reasons.
    (Also it's recommended by the pandas documentation.)
    https://pandas.pydata.org/docs/user_guide/copy_on_write.html
    """

    def __init__(self, data: pd.DataFrame, *, maxlines: int | None = None) -> None:
        """
        Expects a DataFrame with columns
        "title", "difficulty", "chart_constant", "score".
        """
        self._data = data.copy()
        self._data.dropna(inplace=True)
        self._data["ptt"] = get_ptt_delta(self._data["score"])
        self._data["ptt"] += self._data["chart_constant"]

        self._data.sort_values(by="ptt", ascending=False, inplace=True)

        if maxlines is not None:
            self._data = self._data.head(maxlines)

    def get_data(self) -> pd.DataFrame:
        """Return a *copy* of the data sorted by PTT (descending)."""
        return self._data.copy()

    def get_column(self, column: str) -> pd.Series:
        """Return a *copy* of a specific column sorted by PTT (descending)."""
        return self._data[column].copy()

    def get_best_n(self, n: int) -> pd.DataFrame:
        """Return the best-ptt n song entries (copied)."""
        return self._data.head(n).copy()

    @cache
    def get_best_n_pttavg(self, n: int = 30) -> float:
        """Return the average PTT of the best n scores."""
        return self._data.head(n)["ptt"].mean()

    @classmethod
    def from_xlsx(cls, path: str, *args, **kwargs) -> "DataHandler":
        data = pd.read_excel(path)
        data = data.rename(columns={"label": "difficulty", "detail": "chart_constant"})
        return cls(data, *args, **kwargs)
