# Collapsing bound (angle) on the augmented R1 data

Fitted 4 models; protocol docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md part A. Time unit 2000 tokens.

## Diagnostics

                          label    n  divergences  max_rhat     min_ess  flagged
model                                                                           
angle                angle_kept  462            0  1.008927  201.137284    False
angle_theta0  angle_theta0_kept  462            0  1.048122  121.243232    False
ddm                         ddm  462            0  1.015701  274.736416    False
ddm_bounded         ddm_bounded  462            0  1.018223  381.441359    False

## Collapse angle (theta), generalised-logit scale coefficients and back-transformed intercept

theta intercept (link scale): -2.039 [-2.457, -1.709] -> theta for recall questions 0.061 rad [0.011, 0.115]
theta has_code (compute minus recall, link scale): -0.757 [-1.172, -0.392]
Pre-specified rule: collapse established if the recall-question theta interval lies above 0.05 rad -> not established

## Deviation (2026-11-15): stuck chains dropped

For ['angle', 'angle_theta0'] two of four chains never moved (step size adapted to zero, maximum tree depth every iteration). Those chains are dropped and diagnostics above are for the moving chains only (label *_kept); 'stuck_chains' in fit_<model>.csv lists them. The doubled-budget refit was stopped because it cannot repair a chain that never moved. The ESS/r-hat thresholds of the protocol were judged on the kept chains.

## LOO comparison

              rank  elpd_diff   dse  p_worse diag_diff    diag_elpd     p   elpd    se  weight
ddm              0        0.0   0.0      NaN            5 k̂ > 0.70  49.3 -340.0  38.0    0.99
angle            1     -160.0  13.0      1.0            2 k̂ > 0.67  25.3 -500.0  35.0    0.00
ddm_bounded      2     -160.0  12.0      1.0            3 k̂ > 0.70  27.4 -500.0  34.0    0.01
angle_theta0     3     -160.0  14.0      1.0            2 k̂ > 0.67  24.2 -500.0  35.0    0.00

Pareto k > 0.7 counts: {'angle': 1, 'angle_theta0': 2, 'ddm': 5, 'ddm_bounded': 3}

## Posterior predictive: censoring and accuracy by finish length

       model                              how                        cens_step1                          cens_cap               acc_0_6000          acc_6000_12000         acc_12000_20000         acc_20000_30000
       angle hssm.sample_posterior_predictive 0.239 [0.202, 0.278] vs obs 0.427 0.073 [0.016, 0.145] vs obs 0.194 0.84 vs obs 0.95 (n=207) 0.67 vs obs 1.00 (n=32) 0.60 vs obs 0.73 (n=30) 0.63 vs obs 0.60 (n=10)
angle_theta0 hssm.sample_posterior_predictive 0.234 [0.200, 0.273] vs obs 0.427 0.058 [0.000, 0.113] vs obs 0.194 0.84 vs obs 0.95 (n=207) 0.66 vs obs 1.00 (n=32) 0.60 vs obs 0.73 (n=30) 0.58 vs obs 0.60 (n=10)
         ddm hssm.sample_posterior_predictive 0.375 [0.338, 0.410] vs obs 0.427 0.311 [0.194, 0.420] vs obs 0.194 0.93 vs obs 0.95 (n=207) 0.79 vs obs 1.00 (n=32) 0.68 vs obs 0.73 (n=30) 0.66 vs obs 0.60 (n=10)
 ddm_bounded hssm.sample_posterior_predictive 0.235 [0.195, 0.273] vs obs 0.427 0.061 [0.016, 0.129] vs obs 0.194 0.84 vs obs 0.95 (n=207) 0.64 vs obs 1.00 (n=32) 0.57 vs obs 0.73 (n=30) 0.54 vs obs 0.60 (n=10)

## Reading (written 2026-11-15 after the finish stage; ddm_bounded is a post hoc control)

Back-transformed population parameters (posterior means; a and v in network units, t in tokens):

```
model          a_recall  a_compute  v_recall  v_compute  t_recall  t_compute  sigma_q  theta_recall  theta_compute
ddm             0.99      3.08       3.03      0.71       74        376        0.35
ddm_bounded     0.87      2.10       1.69      0.56       80        600        0.67
angle           0.90      2.10       1.70      0.58       104       633        0.69   0.061 [0.011,0.115]   -0.02
angle_theta0    0.87      2.11       1.70      0.58       106       642        0.69   0 (pinned)
```

1. **No collapsing bound.** With the bound free to collapse, the fitted collapse is 0.06 rad on recall questions
   (interval 0.01 to 0.12, so the pre-registered rule "interval above 0.05" is not met) and about zero on compute
   questions. Letting the bound collapse buys nothing out of sample: angle and angle_theta0 tie on LOO (both -500,
   difference well inside its error), and their posterior predictive tables are the same.
2. **The 160-nat gap to the analytical DDM is the parameter range, not the likelihood.** The analytical DDM under the
   network's range (ddm_bounded: a in 0.3-2.5, v in -3..3) lands on the same parameters as the two network fits, the
   same LOO (-500) and the same posterior predictive. So the pretrained angle network is faithful inside its range;
   the problem is that this data wants a compute-question boundary near 3.1 and a recall-question drift near 3.0,
   which is at or beyond the range the network was trained on (a up to 3.0, v up to 3.0). Inside the range, every
   model under-predicts censoring (0.24 vs 0.43 at the 8,192 cap; 0.06 vs 0.19 at 24,576) and over-predicts short-run
   errors (0.84 vs 0.95 below 6,000 tokens); the unrestricted DDM reproduces both (0.38 vs 0.43; 0.31 vs 0.19; 0.93 vs
   0.95). The survival term is not at fault: at the fitted parameters it matches simulation within 0.006.
3. **What this means for the slow-error question.** The cap-experiment pattern (accuracy falling with finish length) is
   reproduced by a fixed-bound DDM with question-level drift variation (sigma_q 0.35), with no need for a bound that
   drops over time. A collapsing bound is not ruled out; it is untestable with the pretrained network on this data
   because R1's fitted parameters sit at the edge of the network's training range. Testing it properly needs either
   a network trained on a wider range (a to ~5, v to ~5) or a likelihood-free fit; both are out of scope here.
4. **Caveats.** The network fits are two chains of 500 draws each (two of four chains failed step-size adaptation
   and were dropped; see the deviation above); the kept chains pass the protocol thresholds. The posterior predictive
   accuracy-by-length bins beyond 12,000 tokens have 30 and 10 observed runs.
