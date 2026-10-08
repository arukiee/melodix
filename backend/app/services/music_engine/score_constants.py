"""
Scoring constants for Melodix practice evaluation.

Thresholds are drawn from:
  "Deep-learning piano performance evaluation" (Nakamura et al., 2015 / Flossmann et al., 2010
  lineage).  Treat these as a *citable starting point* — if real playing tests show they feel
  too strict or too lenient, tune them empirically and note that they were adjusted.

EFQ weights come from a single paper and are not independently verified — treat as provisional.
"""

# ---------------------------------------------------------------------------
# Error-classification thresholds
# ---------------------------------------------------------------------------

# Onset timing tolerance (seconds).  ±30 ms is the JND for expressive micro-timing;
# deviations within this window are NOT penalised.
TIMING_ERROR_THRESHOLD_S: float = 0.030

# Velocity tolerance (MIDI units, 0–127).  7 units ≈ 5 dB difference — below this
# level a listener cannot reliably distinguish dynamic intent.
DYNAMICS_ERROR_THRESHOLD_VEL: int = 7

# ---------------------------------------------------------------------------
# EFQ (Expressiveness Feature Quotient) weights — 0.4 / 0.35 / 0.25
# NOTE: These three weights must sum to 1.0.
# ---------------------------------------------------------------------------

EFQ_WEIGHT_DYNAMIC_VARIANCE: float    = 0.40
EFQ_WEIGHT_TEMPORAL_STABILITY: float  = 0.35
EFQ_WEIGHT_CONSISTENCY: float         = 0.25

# Placeholder value for consistency sub-score (0–1 range).
# KNOWN SIMPLIFICATION: A real note-grouping-consistency measure has not yet
# been implemented.  Replace this constant once grouping analysis is available.
CONSISTENCY_PLACEHOLDER: float = 0.7

# Expected velocity variance range for normalisation.
# A student whose velocities vary by EXPECTED_VEL_VARIANCE MIDI units is scored 1.0.
# Students with more variance are clamped to 1.0; less variance yields a proportionally
# lower score.
EXPECTED_VEL_VARIANCE: float = 400.0   # ≈ std-dev of 20 units across a phrase

# Expected inter-onset interval (IOI) standard deviation for normalisation.
# An IOI std-dev of EXPECTED_IOI_STD seconds is considered "maximally unstable" → score 0.
# Lower std-dev → higher Temporal Stability score.
EXPECTED_IOI_STD_S: float = 0.25
