# Per-question cue slope in the deference DDM fits

Protocol: docs/ANGLE_RANDOM_SLOPE_PROTOCOL.md part B. `v ~ 1 + cue_present + (1 + cue_present|qid)`; the comparison fit is the saved step-coded model without the random slope.

      model_name       model  flagged  slope_sd  slope_sd_lo  slope_sd_hi   heterogeneity  elpd_diff_vs_no_slope  elpd_diff_se          loo_verdict  spearman_slope_vs_control_error  share_q_interval_excludes_0
DeepSeek-R1-0528  Mv_step_rs    False     0.015        0.002        0.032 not established                    0.0          1.10                  tie                           -0.064                         0.00
DeepSeek-R1-0528 Mzv_step_rs    False     0.014        0.002        0.031 not established                    0.0          0.86                  tie                           -0.170                         0.00
       Qwen3-32B  Mv_step_rs    False     0.112        0.083        0.143 not established                  100.0         11.00 favours random slope                           -0.417                         0.11
       Qwen3-32B Mzv_step_rs    False     0.106        0.078        0.138 not established                   50.0         10.00 favours random slope                           -0.376                         0.10
    gpt-oss-120b  Mv_step_rs    False     0.110        0.023        0.190 not established                   10.0          3.20 favours random slope                           -0.279                         0.00
    gpt-oss-120b Mzv_step_rs    False     0.134        0.040        0.221 not established                   10.0          3.80 favours random slope                           -0.203                         0.00

## Population cue effects with (rs) and without (old) the random slope

      model_name       model     v_cue_present_rs    v_cue_present_old       a_cue_present_rs      a_cue_present_old          v_Intercept_rs         v_Intercept_old        z_cue_present_rs      z_cue_present_old
DeepSeek-R1-0528  Mv_step_rs 0.082 [0.068, 0.097] 0.080 [0.067, 0.092]   0.880 [0.660, 1.098]   0.884 [0.665, 1.099] -0.161 [-0.186, -0.138] -0.160 [-0.185, -0.137]                     NaN                    NaN
DeepSeek-R1-0528 Mzv_step_rs 0.057 [0.040, 0.074] 0.055 [0.038, 0.072]   0.713 [0.489, 0.942]   0.714 [0.497, 0.948] -0.161 [-0.188, -0.138] -0.159 [-0.185, -0.135]    0.517 [0.303, 0.724]   0.523 [0.318, 0.755]
       Qwen3-32B  Mv_step_rs 0.181 [0.146, 0.216] 0.128 [0.109, 0.148] -0.036 [-0.160, 0.079]   0.101 [0.002, 0.201] -0.315 [-0.362, -0.265] -0.260 [-0.299, -0.219]                     NaN                    NaN
       Qwen3-32B Mzv_step_rs 0.200 [0.160, 0.239] 0.130 [0.106, 0.152]  0.090 [-0.058, 0.231]  0.109 [-0.028, 0.240] -0.300 [-0.354, -0.249] -0.228 [-0.273, -0.186] -0.294 [-0.490, -0.089] -0.075 [-0.243, 0.118]
    gpt-oss-120b  Mv_step_rs 0.186 [0.132, 0.242] 0.162 [0.123, 0.203] -0.015 [-0.111, 0.091]  0.012 [-0.079, 0.104] -0.516 [-0.602, -0.423] -0.493 [-0.577, -0.411]                     NaN                    NaN
    gpt-oss-120b Mzv_step_rs 0.080 [0.015, 0.147] 0.067 [0.019, 0.117] -0.075 [-0.195, 0.051] -0.061 [-0.177, 0.056] -0.560 [-0.665, -0.450] -0.534 [-0.631, -0.434]    0.671 [0.454, 0.885]   0.670 [0.458, 0.874]
## Reading (written 2026-11-15 after the fits)

All six fits converged at the default budget (no divergences, r-hat at most 1.03, bulk ESS at least 300).

- **DeepSeek-R1**: the question cue-slope SD is 0.015 (0.002 to 0.032) against a population drift effect of 0.08, and LOO is a tie (0 +/- 1). The key moves every question's drift by about the same amount; the population effect is a fair summary.
- **Qwen3-32B**: the slope SD is 0.11 (0.08 to 0.14) against a population effect of 0.18, LOO favours the random slope by 100 +/- 11 (Mv) and 50 +/- 10 (Mzv), and 11% of questions have a slope interval excluding zero. The pre-registered "established" threshold (lower bound above 0.2) was set too high relative to the population effect and is not met, but the LOO rule is met by a wide margin. Adding the slope also changes the population story: the drift effect rises from 0.13 to 0.18-0.20 (outside the earlier interval) and, in the Mzv fit, the starting point moves away from the cued option (-0.29, -0.49 to -0.09; earlier -0.08 with an interval covering zero). Qwen therefore starts slightly more sceptical of the key and is then pushed harder by it, with the push varying by question.
- **gpt-oss-120b**: slope SD 0.11-0.13 with a wide interval (0.02 to 0.22); LOO favours the random slope by 10 +/- 3-4; population effects unchanged.
- **Direction of the heterogeneity**: in all three models the per-question slope correlates negatively with the control error rate (Spearman -0.06/-0.17 for R1, -0.42/-0.38 for Qwen, -0.28/-0.20 for gpt-oss). The key adds the most drift toward the cued answer on questions the model already answers correctly; on questions it already gets wrong the drift is already pointing at the cued option and the key adds little. This is the ceiling-effect form of the knowledge-dominant reading, not a set of specially susceptible questions.
