"""Module B - imports from module C."""

import numpy as np
from cross_module import module_c


def transform(data):
    """Transform data using module C."""
    validated = module_c.validate(data)
    array = np.array(validated)
    return array.tolist()


def process():
    """Process function."""
    return module_c.validate([1, 2, 3])
