"""Module A - imports from module B and external packages."""

import pandas as pd
from cross_module import module_b


def process_with_b(data):
    """Process data using module B."""
    result = module_b.transform(data)
    df = pd.DataFrame(result)
    return df


def helper():
    """Helper function."""
    return "helper"
