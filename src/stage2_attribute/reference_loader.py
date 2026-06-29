"""Load the mining-pool reference list (coinbase tags + payout addresses)."""
import json


def load_reference(path):
    """Return (coinbase_tags, payout_addresses) from a pools.json file.

    encoding="utf-8" is required: some pool tags are non-ASCII (Chinese / emoji),
    and the platform default (cp1252 on Windows) cannot read them.
    """
    with open(path, encoding="utf-8") as f:
        pools = json.load(f)
    return pools["coinbase_tags"], pools["payout_addresses"]
