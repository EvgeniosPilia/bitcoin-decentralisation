# Actor-Aware Measurement of Bitcoin Decentralisation

MSc dissertation project. Measures how sensitive Bitcoin consensus-layer
decentralisation metrics (Nakamoto coefficient, HHI, Gini, Shannon entropy,
CR3/CR5) are to block-attribution choices, and whether structural changes in
decentralisation over time are robust to those choices or artifacts of them.

## Setup
1. Python 3.12 — create a venv and `pip install -r requirements.txt`
2. A Google Cloud account with BigQuery access
3. Authenticate (no key file needed):  `gcloud auth application-default login`

## Layout
- `src/stage1_extract/`   pull raw block data from BigQuery
- `src/stage2_attribute/` map blocks to mining pools (tag + address matching)
- `src/stage3_metrics/`   compute decentralisation metrics over time windows
- `src/common/`           shared utilities
- `data/`                 raw / intermediate / derived (gitignored, regenerable)
- `notebooks/`            exploratory analysis
- `figures/`              generated figures
- `tests/`                pytest suite
- `thesis/`               LaTeX source
