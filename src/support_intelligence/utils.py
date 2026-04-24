from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def month_starts(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start=start, end=end, freq="MS")


def clamp(value: float, low: float, high: float) -> float:
    return float(max(low, min(high, value)))


def normalize_series(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    minimum = series.min()
    maximum = series.max()
    if np.isclose(maximum, minimum):
        return pd.Series(np.full(len(series), 50.0), index=series.index)
    return ((series - minimum) / (maximum - minimum)) * 100


def slugify(value: str) -> str:
    return (
        value.lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )


def safe_mode(values: Iterable[str], default: str = "Unknown") -> str:
    series = pd.Series(list(values))
    if series.empty:
        return default
    mode = series.mode()
    if mode.empty:
        return default
    return str(mode.iloc[0])


def export_dataframe(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)

