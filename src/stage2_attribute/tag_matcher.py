"""Attribute a block to a pool by its coinbase tag."""
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
