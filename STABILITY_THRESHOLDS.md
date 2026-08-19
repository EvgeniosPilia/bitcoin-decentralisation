# Pre-Registration: Temporal Stability Thresholds (RQ3)

**Committed BEFORE running the stability analysis.** The git commit timestamp of
this file is the pre-registration record. The thresholds below are fixed and will
not be changed in response to results.

## Question

Every metric so far is computed on **monthly** windows. RQ3 asks whether the
decentralisation findings are an artifact of that choice: do they hold at **daily,
weekly, and quarterly** granularity, or dissolve into sampling noise at finer
scales? This is the direct tie-in to Milad, Ovezik, Karakostas & Woods (2024):
finer windows contain fewer blocks, so each metric estimate is noisier.

## Fixed analysis settings

- **Attribution scenario held fixed** at the baseline **H1 (tag-only) / U2 (exclude
  unknown)**. Only temporal granularity is varied, so its effect is isolated.
- **Granularities:** daily (D), weekly (W), quarterly (Q), each compared to the
  **monthly (M)** baseline.
- **Metrics for the CV test:** HHI, Shannon entropy, CR3, CR5 (all continuous).
  **Nakamoto is reported separately** (it is integer-valued, so CV is ill-behaved
  on it); its threshold-brittleness is described qualitatively, not CV-tested.

## Decision rule 1 — sampling stability (CV)

- **Measure:** window-to-window coefficient of variation (std / mean) of each
  metric, computed over the **most recent 24 complete months** in the data — a
  period of relatively stable concentration, chosen so the CV reflects sampling
  noise rather than real trend.
- **Primary threshold:** a granularity is "stable" for a metric if **CV < 0.15**.
- **No averaging of thresholds** (a threshold is a decision rule, not a quantity to
  average). Instead, report the **raw CV value** for every metric x granularity, and
  a **sensitivity strip** giving pass/fail at **0.10 / 0.15 / 0.20**, so the
  robustness of the conclusion to the cutoff is fully transparent.

## Decision rule 2 — trend survival (BOTH must hold)

A granularity "preserves the trend" only if **both**:

- **(a) Correlation:** Spearman rank correlation **rho > 0.8** between that
  granularity's series and the monthly baseline, after aligning to common monthly
  periods (resample the finer series to monthly means before correlating).
- **(b) Change-point agreement:** the salient change-points detected by **PELT (l2
  cost; penalty tuned to yield the 2-3 most salient breaks on the monthly
  baseline, the same penalty applied at each granularity)** each have a matching
  change-point **within +/- 2 months** at the compared granularity.

## Verdict

A granularity is **"usable"** if it meets the CV threshold (rule 1) **and** both
trend-survival criteria (rule 2). The result will report, per metric and per
granularity, the raw numbers and the pass/fail, and state the **finest granularity
that remains usable**.


