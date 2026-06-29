"""Tests for the decentralisation metrics, checked against hand-computed values."""
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
