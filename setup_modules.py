"""Scaffold the src/ modules, tests, and pyproject.toml for the pipeline.

Run ONCE from the repo root (with your venv active):

    python setup_modules.py

Then:

    pip install -e .          # makes the modules importable everywhere
    pytest -q                 # run the tests

Cross-platform: plain Python, no bash needed.
"""
import os

FILES = {

"pyproject.toml": '''[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "bitcoin-decentralisation"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.2",
    "numpy>=1.26",
    "pyarrow>=17.0",
    "matplotlib>=3.8",
]

[tool.setuptools.packages.find]
where = ["src"]
''',

"src/stage2_attribute/__init__.py": '''"""Stage 2: attribute blocks to mining pools."""
''',

"src/stage2_attribute/reference_loader.py": '''"""Load the mining-pool reference list (coinbase tags + payout addresses)."""
import json


def load_reference(path):
    """Return (coinbase_tags, payout_addresses) from a pools.json file.

    encoding="utf-8" is required: some pool tags are non-ASCII (Chinese / emoji),
    and the platform default (cp1252 on Windows) cannot read them.
    """
    with open(path, encoding="utf-8") as f:
        pools = json.load(f)
    return pools["coinbase_tags"], pools["payout_addresses"]
''',

"src/stage2_attribute/tag_matcher.py": '''"""Attribute a block to a pool by its coinbase tag."""
import re


def decode_coinbase(hex_str):
    """Decode a coinbase_param hex string to UTF-8 text (keeps non-ASCII tags)."""
    if not hex_str:
        return ""
    try:
        return bytes.fromhex(hex_str).decode("utf-8", errors="ignore")
    except (ValueError, TypeError):
        return str(hex_str)


class TagMatcher:
    """Match coinbase text against a reference list of tag -> pool.

    The reference patterns are compiled into one regex, longest-first, so the
    most specific tag wins on nested cases (e.g. /ViaBTC/Sub/ over /ViaBTC/).
    """

    def __init__(self, coinbase_tags):
        ordered = sorted(coinbase_tags.items(), key=lambda kv: len(kv[0]), reverse=True)
        self._tag_to_pool = {tag: meta["name"] for tag, meta in coinbase_tags.items()}
        self._re = (
            re.compile("(" + "|".join(re.escape(tag) for tag, _ in ordered) + ")")
            if ordered else None
        )

    def match(self, coinbase_text):
        """Return the pool name, or None if no tag matches."""
        if not self._re:
            return None
        m = self._re.search(coinbase_text)
        return self._tag_to_pool[m.group(1)] if m else None

    def match_hex(self, coinbase_param):
        """Decode a hex coinbase_param, then match it."""
        return self.match(decode_coinbase(coinbase_param))
''',

"src/stage2_attribute/address_matcher.py": '''"""Attribute a block to a pool by its coinbase payout addresses."""
from collections import Counter


class AddressMatcher:
    """Match output addresses against a reference list of address -> pool."""

    def __init__(self, payout_addresses):
        self._addr_to_pool = {addr: meta["name"] for addr, meta in payout_addresses.items()}

    def match(self, addresses):
        """Return the most common matching pool, or None if none match."""
        if addresses is None or len(addresses) == 0:
            return None
        names = [self._addr_to_pool[a] for a in addresses if a in self._addr_to_pool]
        if not names:
            return None
        return Counter(names).most_common(1)[0][0]
''',

"src/stage2_attribute/confidence.py": '''"""Combine tag and address attributions into a confidence tier.

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
''',

"src/stage3_metrics/__init__.py": '''"""Stage 3: decentralisation metrics over time."""
''',

"src/stage3_metrics/decentralisation.py": '''"""Decentralisation metrics. Each takes a count-per-entity mapping (or iterable
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
''',

"src/stage3_metrics/windowing.py": '''"""Compute decentralisation metrics over rolling time windows."""
import pandas as pd

from .decentralisation import all_metrics


def metrics_over_time(attributed, period="M", unknown="exclude"):
    """Long-format metric time series.

    Parameters
    ----------
    attributed : DataFrame with columns [timestamp, pool]
    period : "D", "W", or "M" -- temporal granularity (the RQ3 knob)
    unknown : "exclude" (U2) or "single" (U1) -- treatment of unattributed blocks (a D3 axis)
    """
    df = attributed.copy()
    df["window"] = pd.to_datetime(df["timestamp"]).dt.to_period(period).dt.to_timestamp()
    if unknown == "exclude":
        df = df[df["pool"] != "unknown"]
    rows = []
    for window, group in df.groupby("window"):
        counts = group["pool"].value_counts().to_dict()
        for name, value in all_metrics(counts).items():
            rows.append({"window": window, "metric": name, "value": value,
                         "period": period, "unknown": unknown})
    return pd.DataFrame(rows)
''',

"src/common/__init__.py": '''"""Shared utilities."""
''',

"tests/test_metrics.py": '''"""Tests for the decentralisation metrics, checked against hand-computed values."""
import pytest
from stage3_metrics.decentralisation import (
    nakamoto, hhi, gini, shannon_entropy, concentration_ratio)


def test_uniform_four():
    c = {"a": 25, "b": 25, "c": 25, "d": 25}
    assert nakamoto(c) == 3
    assert hhi(c) == pytest.approx(0.25)
    assert gini(c) == pytest.approx(0.0)
    assert shannon_entropy(c) == pytest.approx(2.0)        # log2(4)
    assert concentration_ratio(c, 3) == pytest.approx(0.75)


def test_two_equal():
    c = {"a": 50, "b": 50}
    assert nakamoto(c) == 2
    assert hhi(c) == pytest.approx(0.5)
    assert shannon_entropy(c) == pytest.approx(1.0)


def test_monopoly():
    c = {"a": 100}
    assert nakamoto(c) == 1
    assert hhi(c) == pytest.approx(1.0)
    assert shannon_entropy(c) == pytest.approx(0.0)


def test_skewed_is_concentrated():
    c = {"big": 97, "x": 1, "y": 1, "z": 1}
    assert nakamoto(c) == 1
    assert hhi(c) > 0.9
    assert shannon_entropy(c) < 0.5
''',

"tests/test_attribution.py": '''"""Tests for tag/address matching and the confidence scheme.

Uses a tiny hermetic reference list (no downloaded file or network needed).
chr() is used for non-ASCII tags so this source file stays pure ASCII.
"""
import pandas as pd
from stage2_attribute.tag_matcher import TagMatcher, decode_coinbase
from stage2_attribute.address_matcher import AddressMatcher
from stage2_attribute.confidence import confidence_frame

TAGS = {
    "/F2Pool/": {"name": "F2Pool"},
    "/ViaBTC/": {"name": "ViaBTC"},
    "/ViaBTC/Sub/": {"name": "SubPool"},          # nested -> longest wins
    "Mined by AntPool": {"name": "AntPool"},
}
ADDRS = {"addrF2": {"name": "F2Pool"}, "addrAnt": {"name": "AntPool"}}


def test_tag_basic():
    tm = TagMatcher(TAGS)
    assert tm.match("/F2Pool/") == "F2Pool"
    assert tm.match("Mined by AntPool") == "AntPool"
    assert tm.match("no tag here") is None


def test_tag_nested_longest_wins():
    tm = TagMatcher(TAGS)
    assert tm.match("/ViaBTC/Sub/") == "SubPool"
    assert tm.match("/ViaBTC/") == "ViaBTC"


def test_decode_is_utf8():
    # U+9C7C is the 3 UTF-8 bytes e9 b1 bc; an ASCII decode would mangle it.
    assert decode_coinbase("e9b1bc") == chr(0x9C7C)


def test_tag_matches_non_ascii():
    fish = chr(0x1F41F)
    tm = TagMatcher({fish: {"name": "F2Pool"}, "/ViaBTC/": {"name": "ViaBTC"}})
    assert tm.match(fish) == "F2Pool"


def test_address_matcher():
    am = AddressMatcher(ADDRS)
    assert am.match(["addrF2"]) == "F2Pool"
    assert am.match(["unknown_addr"]) is None
    assert am.match([]) is None
    assert am.match(None) is None


def test_confidence_tiers_are_na_safe():
    tag = pd.Series(["AntPool", "F2Pool", "ViaBTC", None, "Foundry"])
    addr = pd.Series(["AntPool", None, "X", None, None])
    pool, conf = confidence_frame(tag, addr)
    assert list(conf) == ["HIGH", "TAG_ONLY", "CONFLICT", "UNKNOWN", "TAG_ONLY"]
    assert list(pool) == ["AntPool", "F2Pool", "ViaBTC", "unknown", "Foundry"]
''',
}


def main():
    created, skipped = [], []
    for path, content in FILES.items():
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            skipped.append(path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)

    print("Created:")
    for p in created:
        print("  +", p)
    if skipped:
        print("Skipped (already existed):")
        for p in skipped:
            print("  .", p)
    print("\nNext:")
    print("  pip install -e .")
    print("  pytest -q")


if __name__ == "__main__":
    main()
