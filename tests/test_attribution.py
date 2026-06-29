"""Tests for tag/address matching and the confidence scheme.

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
