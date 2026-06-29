"""Attribute a block to a pool by its coinbase payout addresses."""
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
