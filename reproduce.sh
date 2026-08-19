#!/usr/bin/env bash
#
# reproduce.sh — full reproduction of
#   "Actor-Aware and Robust Measurement of Bitcoin Mining Decentralisation"
#
# Runs the pipeline end to end: extraction (Stage 1), attribution (Stage 2),
# metrics and analyses (Stage 3). Each stage executes a notebook in place, so
# outputs and figures are regenerated exactly as reported in the dissertation.
#
# Usage:
#   ./reproduce.sh            # full run (Stage 1 requires BigQuery credentials)
#   ./reproduce.sh --cached   # skip Stage 1, use the archived raw data
#
# Requirements:
#   - Python 3.11+ with the project installed:  pip install -e .
#   - For Stage 1 only: a Google Cloud project and
#       gcloud auth application-default login
#     Stage 1 queries the public bigquery-public-data.crypto_bitcoin dataset.
#     Cost is bounded by filtering on the month-partition column; expect a few
#     GB scanned per year of address data. ALWAYS dry-run first if modifying.
#   - With --cached, no credentials or network access are needed.
#
# Runtime: Stage 1 ~30-60 min (network-bound). Stages 2-3 ~20-30 min.

set -euo pipefail

CACHED=0
if [[ "${1:-}" == "--cached" ]]; then
    CACHED=1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

NB_DIR="notebooks"
mkdir -p data/raw data/derived figures

run_nb () {
    local nb="$1"
    local label="$2"
    if [[ ! -f "$NB_DIR/$nb" ]]; then
        echo "  !! missing notebook: $NB_DIR/$nb" >&2
        exit 1
    fi
    echo ""
    echo "=== $label"
    echo "    ($nb)"
    jupyter nbconvert \
        --to notebook \
        --execute \
        --inplace \
        --ExecutePreprocessor.timeout=7200 \
        "$NB_DIR/$nb"
}

echo "==========================================================="
echo " Reproducing: Actor-Aware and Robust Measurement of"
echo "              Bitcoin Mining Decentralisation"
echo "==========================================================="

# ---------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------
echo ""
echo "--- Preflight ---"
python -c "import pandas, numpy, matplotlib, pyarrow" \
    || { echo "Missing core dependencies. Run: pip install -e ."; exit 1; }
echo "core dependencies OK"

python -c "import networkx" 2>/dev/null \
    && echo "networkx OK (operator clustering enabled)" \
    || echo "networkx not found — Stage 3f will install it on first run"

if [[ $CACHED -eq 0 ]]; then
    python -c "from google.cloud import bigquery" 2>/dev/null \
        || { echo "google-cloud-bigquery not installed. Either 'pip install google-cloud-bigquery' or re-run with --cached"; exit 1; }
    echo "BigQuery client OK"
fi

echo ""
echo "--- Unit tests ---"
python -m pytest -q tests/ || { echo "Tests failed — aborting."; exit 1; }

# ---------------------------------------------------------------
# Stage 1 — extraction
# ---------------------------------------------------------------
if [[ $CACHED -eq 1 ]]; then
    echo ""
    echo "=== Stage 1 SKIPPED (--cached)"
    if [[ ! -f data/raw/raw_blocks_full.parquet ]]; then
        echo "  !! data/raw/raw_blocks_full.parquet not found."
        echo "     Download the archived data (see README / DataShare DOI)" >&2
        exit 1
    fi
    echo "    using archived data/raw/raw_blocks_full.parquet"
else
    run_nb "fullhistory_tags.ipynb"      "Stage 1a — full-history block + coinbase-tag extraction"
    run_nb "extract_addresses.ipynb"     "Stage 1b — coinbase payout-address extraction"
fi

# ---------------------------------------------------------------
# Stage 2/3 — attribution, metrics, analyses
# ---------------------------------------------------------------
run_nb "metrics_over_time.ipynb"         "Stage 2/3 — attribution and the baseline trajectory (Fig 4.2)"
run_nb "sensitivity_unknown.ipynb"       "Stage 3a — unknown-block sensitivity, U1-U3 (RQ2)"
run_nb "sensitivity_full.ipynb"          "Stage 3b — full H1-H5 x U1-U3 grid (RQ2, Table 4.2, Fig 4.3)"
run_nb "a2_actor_threshold.ipynb"        "Stage 3c — actor-definition sweep, A2 (RQ1, Fig 4.4)"
run_nb "interlist_conflict.ipynb"        "Stage 3d — btc.com vs mempool.space inter-list agreement (Fig 4.5)"
run_nb "stability_granularity.ipynb"     "Stage 3e — temporal stability D/W/M/Q (RQ3, Fig A.1)"
run_nb "hr2_bootstrap_ci.ipynb"          "Stage 3f — bootstrap sampling CIs (Fig 4.6)"
run_nb "changepoint_robustness.ipynb"    "Stage 3g — change-point robustness (RQ4, Fig 4.7)"
run_nb "a3_operator_clustering.ipynb"    "Stage 3h — operator clustering, A3 upper bound (§5.1)"

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
echo ""
echo "==========================================================="
echo " Reproduction complete."
echo ""
echo " Derived data:  data/derived/"
ls -1 data/derived/ 2>/dev/null | sed 's/^/   - /' || true
echo ""
echo " Figures:       figures/"
ls -1 figures/*.png 2>/dev/null | sed 's|.*/|   - |' || true
echo ""
echo " Pre-registered thresholds: STABILITY_THRESHOLDS.md"
echo "==========================================================="
