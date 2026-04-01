"""External module - imports from external packages."""

import numpy as np
import pandas as pd


def analyze(data: list):
    """Analyze data using external packages."""
    df = pd.DataFrame(data)
    array = np.array(data)
    return df, array


def process_series(series: pd.Series):
    """Process pandas series."""
    return series.mean()
