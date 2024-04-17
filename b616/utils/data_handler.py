from functools import cache

import pandas as pd

from b616.utils.arcaea_ptt import get_ptt_delta


class DataHandler:
    """A class to handle Arcaea score data.
    The data returned is sorted by PTT in descending order.

    Note that the data shall not be mutated after initialization.
    If you want to modify the data, you should get the data, modify it,
    and then create a new DataHandler object with the modified data.

    NOTE: All returned data are copies of the original data, so they are safe to modify.
    This class is coded with the assumption that copy-on-write mode is enabled.
    Correctness probably still holds without copy-on-write mode, but performance may be worse.

    Using Copy-On-Write mode in pandas is strongly recommended for performance reasons.
    (Also it's recommended by the pandas documentation.)
    https://pandas.pydata.org/docs/user_guide/copy_on_write.html
    """

    def __init__(self, data: pd.DataFrame, *, maxlines: int | None = None) -> None:
        """
        Expects a DataFrame with columns
        "title", "difficulty", "chart_constant", "score".
        """
        self._data = data.dropna().copy()
        self._data["ptt"] = get_ptt_delta(self._data["score"])
        self._data["ptt"] += self._data["chart_constant"]

        self._data.sort_values(by="ptt", ascending=False, inplace=True)

        if maxlines is not None:
            self._data = self._data.head(maxlines)

    @property
    def size(self) -> int:
        """Return the number of data entries."""
        return self._data.shape[0]

    @property
    def data(self) -> pd.DataFrame:
        """Return the data (copied)."""
        return self._data.copy()

    def get_best_n(self, n: int | None = None) -> pd.DataFrame:
        """Return the best-ptt n song entries (copied)."""
        if n is None:
            return self._data.copy()
        return self._data.head(n).copy()

    @cache
    def get_best_n_pttavg(self, n: int | None = None) -> float:
        """Return the average PTT of the best n scores."""
        if n is None:
            return self._data["ptt"].mean()
        return self._data.head(n)["ptt"].mean()

    @classmethod
    def from_xlsx(cls, path: str, *args, **kwargs) -> "DataHandler":
        data = pd.read_excel(path)
        data = data.rename(columns={"label": "difficulty", "detail": "chart_constant"})
        return cls(data, *args, **kwargs)
