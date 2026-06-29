"""Decentralisation metrics. Each takes a count-per-entity mapping (or iterable
of counts) and returns one number.

Higher HHI / Gini / CR  -> more concentrated.
Higher Nakamoto / entropy -> more decentralised.
"""
import numpy as np


def _shares(counts):
    vals = np.asarray(list(counts.values()) if isinstance(counts, dict) else list(counts),
                      dtype=float)
    vals = vals[vals > 0]
    total = vals.sum()
    return vals / total if total > 0 else vals


def nakamoto(counts):
    """Minimum number of entities jointly holding more than 50%."""
    s = sorted(_shares(counts), reverse=True)
    cum = 0.0
    for i, x in enumerate(s, 1):
        cum += x
        if cum > 0.5:
            return i
    return len(s) if s else float("nan")


def hhi(counts):
    """Herfindahl-Hirschman Index = sum of squared shares, range [1/n, 1].

    (Multiply by 10000 for the antitrust convention.)
    """
    s = _shares(counts)
    return float(np.sum(s ** 2)) if len(s) else float("nan")


def gini(counts):
    """Gini coefficient of the share distribution. Higher = more unequal."""
    s = np.sort(_shares(counts))
    n = len(s)
    if n == 0:
        return float("nan")
    i = np.arange(1, n + 1)
    return float((2 * np.sum(i * s)) / (n * s.sum()) - (n + 1) / n)


def shannon_entropy(counts, base=2):
    """Shannon entropy in bits, range [0, log2(n)]. Higher = more decentralised."""
    s = _shares(counts)
    s = s[s > 0]
    return float(-np.sum(s * (np.log(s) / np.log(base)))) if len(s) else float("nan")


def concentration_ratio(counts, k=3):
    """Combined share of the top k entities (CR3, CR5, ...)."""
    s = sorted(_shares(counts), reverse=True)
    return float(sum(s[:k]))


def all_metrics(counts):
    """All metrics as a dict, for one distribution."""
    return {
        "nakamoto": nakamoto(counts),
        "hhi": hhi(counts),
        "gini": gini(counts),
        "shannon": shannon_entropy(counts),
        "cr3": concentration_ratio(counts, 3),
        "cr5": concentration_ratio(counts, 5),
    }
