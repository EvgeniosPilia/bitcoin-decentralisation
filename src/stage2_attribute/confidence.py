"""Combine tag and address attributions into a confidence tier.

NA-safe by design: a non-match is a missing value (None / NaN) and is tested
with pandas null checks, never Python truthiness. (Truthiness silently breaks
because NaN is truthy -- the bug that mislabelled every no-address block.)
"""
import numpy as np
import pandas as pd

TIERS = ("HIGH", "CONFLICT", "TAG_ONLY", "ADDR_ONLY", "UNKNOWN")


def confidence_frame(tag_pool, addr_pool):
    """Vectorised tiering for whole columns.

    Parameters
    ----------
    tag_pool, addr_pool : pandas.Series
        Pool name per block from each method; missing where the method did not match.

    Returns
    -------
    (pool, confidence) : two pandas.Series
        Final pool label and the confidence tier for each block.
    """
    has_tag = tag_pool.notna()
    has_addr = addr_pool.notna()
    confidence = np.select(
        [has_tag & has_addr & (tag_pool == addr_pool),
         has_tag & has_addr & (tag_pool != addr_pool),
         has_tag & ~has_addr,
         ~has_tag & has_addr],
        ["HIGH", "CONFLICT", "TAG_ONLY", "ADDR_ONLY"],
        default="UNKNOWN",
    )
    pool = np.where(has_tag, tag_pool, np.where(has_addr, addr_pool, "unknown"))
    return (pd.Series(pool, index=tag_pool.index),
            pd.Series(confidence, index=tag_pool.index))
