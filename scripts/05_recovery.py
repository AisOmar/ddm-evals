"""Recovery simulations (plan v2, phase 4), calibrated to the 2026-10-07 pilot.

Truth ranges (pilot, DDM time = tokens/100): accuracy ~0.76 overall (0.83 prose / 0.69 code questions);
median rt ~2-3 prose, ~6.5-9.5 code; thorough instruction lengthens by ~1.4x with flat accuracy; a 21%
zero-token share in plain_concise (one-line replies, ~88% correct = fast confident answers on easy
questions, NOT guesses); position bias: chose-A 0.54, acc 0.80 vs 0.73 when correct is A vs B.

Stages (--stage):
  param     4.1  drift-only vs boundary-only scaffold truth; does the fit assign the effect to the right parameter?
  repeats   4.1  5 / 10 / 20 repeats per question at n_questions: interval width + coverage -> full-run sample size
  scaling   4.2  all durations x1.5, choices kept -> expect v/sqrt(k), a*sqrt(k), t*k (same DDM, not a non-DDM generator)
  censoring 4.1  heavy censoring: drop censored rows vs the deadline likelihood P(T>C) (scripts/ddm_censoring.py; HSSM's own
                 omission network for the ddm is not downloadable as of 2026-10-07)
  bias      1.4  option-coded sensitivity fit recovers the starting-point bias z=0.55
  model     4.3  non-DDM generators (fixed budget, answer flip, lognormal+logistic): spurious condition effects?
  all

Every simulated dataset goes through pipeline() -- the same exclusions 03_parse_logs.py applies to real data
(zero-token traces are a separate category; censored rows enter the likelihood, never dropped silently).

usage: python scripts/05_recovery.py --stage all --quick          # ~30-60 min on a laptop
       python scripts/05_recovery.py --stage param                # config draws/tune/chains
Outputs: results/recovery/<stage>.csv (one row per parameter per fit) and results/recovery/REPORT.md
"""
import argparse, json, pathlib, re, time, warnings
import numpy as np, pandas as pd, yaml, hssm, arviz as az
from ddm_censoring import logp_ddm_survival_op
from design import correct_is_a
warnings.filterwarnings("ignore")

cfg = yaml.safe_load(open("config.yaml"))
SEED = cfg["study"]["seed"]
COND = list(cfg["conditions"])
C_STUDY = cfg["model"]["max_tokens"] / cfg["measurement"]["rt_unit_tokens"]   # cutoff in DDM time units (81.92)
OUT = pathlib.Path("results/recovery"); OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- truth, calibrated to the pilot
# HSSM/ssms DDM: boundaries at +/-a (a = half-separation), so P(correct) = 1/(1+exp(-2 v a)), mean DT = (a/v) tanh(v a).
# prose: acc .83, median rt ~1.8 -> v*a = 0.79, (a/v)tanh(va) ~ 1.9 ; code: acc .69, median rt ~7 -> v*a = 0.40, mean DT ~7
BASE = dict(v=0.52, a=1.51, t=0.5)
CODE = dict(v=-0.37, a=1.8, t=4.0)          # has_code effects: additive on v, MULTIPLICATIVE on a and t (log links in the fit)
D_A = 1.33                                  # boundary-only scaffold effect, multiplicative (~ +0.5 on a)
MAX_T = 400.0                               # simulator horizon (ssms default 20 would truncate code questions)
K_THOROUGH = 1.4                            # thorough = pure time scaling (longer, same accuracy), the pilot pattern
P_CODE = 0.44                               # share of code questions in WMDP-cyber (pilot sample)
SD_Q = 0.25                                 # per-question drift sd (accuracy spread 0.5-1.0 in the pilot)
P_ZERO = 0.21                               # zero-token share in plain_concise
Z_BIAS = 0.55                               # starting point toward option A (option coding)


def truth_table(scaffold_effect="drift", d_v=0.15, d_a=D_A):
    """condition -> dict(v, a, t) for a prose question with zero random effect. Thorough = scale k."""
    out = {}
    for c in COND:
        v, a, t = BASE["v"], BASE["a"], BASE["t"]
        if c.startswith("sbs"):
            if scaffold_effect == "drift": v += d_v
            elif scaffold_effect == "boundary": a *= d_a
        if c.endswith("thorough"):
            v, a, t = v / np.sqrt(K_THOROUGH), a * np.sqrt(K_THOROUGH), t * K_THOROUGH
        out[c] = dict(v=v, a=a, t=t)
    return out


def simulate(n_q, reps, truth, rng, z=Z_BIAS, p_zero=P_ZERO, code_fx=CODE, sd_q=SD_Q):
    """Option-coded DDM generator mirroring the real design: balanced correct-is-A within question, has_code
    covariate, per-question drift effect, position bias z, and zero-token traces in plain_concise.
    Returns rows with the same columns 03_parse_logs.py produces (rt, response in ACCURACY coding, ...)."""
    has_code = rng.random(n_q) < P_CODE
    u = rng.normal(0, sd_q, n_q)
    rows = []
    for q in range(n_q):
        for c in COND:
            th = truth[c]
            v = th["v"] + u[q] + (code_fx["v"] if has_code[q] else 0.0)
            a = th["a"] * (code_fx["a"] if has_code[q] else 1.0)
            t = th["t"] * (code_fx["t"] if has_code[q] else 1.0)
            for r in range(reps):
                correct_is_A = correct_is_a(f"q{q:03d}", c, r, COND, SEED)
                v_signed = v if correct_is_A else -v              # upper boundary = option A
                sim = hssm.simulate_data(model="ddm", theta=dict(v=v_signed, a=a, z=z, t=t), size=1,
                                         random_state=int(rng.integers(2**31 - 1)), max_t=MAX_T)
                chose_A = sim.response.iloc[0] > 0
                correct = (chose_A == correct_is_A)
                rows.append(dict(qid=f"q{q:03d}", condition=c, scaffold=c.split("_")[0], instruction=c.split("_")[1],
                                 rep=r, correct_is_A=correct_is_A, has_code=bool(has_code[q]), v_true=v,
                                 rt=float(sim.rt.iloc[0]), chosen="A" if chose_A else "B", correct=bool(correct),
                                 outcome="answered"))
    df = pd.DataFrame(rows)
    # zero-token traces: plain_concise only, more likely on easy (high-drift) questions, 85% correct, rt = 0
    if p_zero > 0:
        pc = df[df.condition == "plain_concise"]
        w = np.exp(2.0 * pc.v_true.values); w /= w.sum()
        idx = rng.choice(pc.index, size=int(round(p_zero * len(pc))), replace=False, p=w)
        df.loc[idx, "outcome"] = "zero_tokens"; df.loc[idx, "rt"] = 0.0
        df.loc[idx, "correct"] = rng.random(len(idx)) < 0.85         # bare-letter replies were 85% correct in the pilot
    df["response"] = np.where(df.correct, 1, -1)
    return df


def pipeline(df, C=C_STUDY, censor_mode="deadline"):
    """What 03/06 do to real data. Zero-token traces leave the DDM data (separate category). Rows with
    rt > C are censored: 'deadline' codes them rt=-999 with a deadline column (HSSM likelihood P(T>C));
    'drop' removes them (the wrong thing, used as the comparison in the censoring check)."""
    d = df[df.outcome == "answered"].copy()
    cens = d.rt > C
    d["censored"] = cens
    if censor_mode == "drop":
        d = d[~cens].copy()
    else:
        d.loc[cens, "rt"] = -999.0
        d["deadline"] = float(C)
    return d


def fit(d, draws, tune, chains, with_code=True, option_coding=False, deadline=False):
    cov = " + has_code" if with_code else ""
    if option_coding:
        d = d.copy(); d["response"] = np.where(d.chosen == "A", 1, -1); d["stim"] = np.where(d.correct_is_A, 1, -1)
        include = [{"name": "v", "formula": f"v ~ 0 + stim + stim:scaffold + stim:instruction + stim:scaffold:instruction{(' + stim:has_code' if with_code else '')} + (0 + stim|qid)"},
                   {"name": "a", "formula": f"a ~ 1 + scaffold*instruction{cov}"},
                   {"name": "t", "formula": f"t ~ 1 + scaffold*instruction{cov}"},
                   {"name": "z", "formula": "z ~ 1"}]
        kw = {}
    else:
        include = [{"name": "v", "formula": f"v ~ 1 + scaffold*instruction{cov} + (1|qid)"},
                   {"name": "a", "formula": f"a ~ 1 + scaffold*instruction{cov}"},
                   {"name": "t", "formula": f"t ~ 1 + scaffold*instruction{cov}"}]
        kw = {"z": 0.5}
    cols = ["rt", "response", "qid", "scaffold", "instruction", "has_code"] + (["stim"] if option_coding else []) + (["deadline"] if deadline else [])
    d = d[cols].copy(); d["has_code"] = d.has_code.astype(int)
    if deadline:
        kw.update(missing_data=True, deadline=True, loglik_missing_data=logp_ddm_survival_op)   # analytical P(T>C), see ddm_censoring.py
    # log links on a and t (logit on z) keep them positive; identity on v. Contrasts for a, t are therefore log-ratios.
    m = hssm.HSSM(data=d, model="ddm", include=include, p_outlier=None, link_settings="log_logit", **kw)
    t0 = time.time()
    idata = m.sample(draws=draws, tune=tune, chains=chains, cores=min(chains, 4), progressbar=False, target_accept=0.95)
    sec = time.time() - t0
    s = az.summary(idata, kind="all", ci_prob=0.94, ci_kind="hdi")
    ci = [c for c in s.columns if c.startswith(("hdi", "eti"))]; lo, hi = ci[0], ci[1]     # arviz 1.x names e.g. hdi_3.0%
    s = s.rename(columns={lo: "hdi_3%", hi: "hdi_97%"})
    s = s.loc[[i for i in s.index if i[:2] in ("v_", "a_", "t_", "z_") and "offset" not in i and not re.search(r"\|qid\[", i)]]
    s["seconds"] = sec; s["n_trials"] = len(d); s["divergences"] = int(idata.sample_stats.diverging.sum())
    return s


def expected(truth, with_code=True, k=1.0):
    """Posterior terms -> true values under treatment coding (plain/concise reference, prose question).
    k = measurement scaling applied after simulation (4.2)."""
    ref, sbs, tho, both = truth["plain_concise"], truth["sbs_concise"], truth["plain_thorough"], truth["sbs_thorough"]
    # v: identity link, scaling divides by sqrt(k). a, t: log link, so terms are log-ratios; scaling adds to the intercept only.
    sc = {"v": lambda x: x / np.sqrt(k), "a": lambda x: np.log(x * np.sqrt(k)), "t": lambda x: np.log(x * k)}
    e = {}
    for p in ("v", "a", "t"):
        f = sc[p]
        e[f"{p}_Intercept"] = f(ref[p])
        e[f"{p}_scaffold[sbs]"] = f(sbs[p]) - f(ref[p])
        e[f"{p}_instruction[thorough]"] = f(tho[p]) - f(ref[p])
        e[f"{p}_scaffold:instruction[sbs, thorough]"] = f(both[p]) - f(sbs[p]) - f(tho[p]) + f(ref[p])
        if with_code: e[f"{p}_has_code"] = CODE["v"] / np.sqrt(k) if p == "v" else np.log(CODE[p])
    e["v_1|qid_sigma"] = SD_Q / np.sqrt(k)
    return e


def record(stage, label, s, exp, extra=None):
    rows = []
    for name, r in s.iterrows():
        tv = exp.get(name, np.nan)
        rows.append(dict(stage=stage, fit=label, param=name, true=tv, mean=r["mean"], sd=r["sd"], hdi3=r["hdi_3%"], hdi97=r["hdi_97%"],
                         covered=(r["hdi_3%"] <= tv <= r["hdi_97%"]) if np.isfinite(tv) else np.nan, r_hat=r.get("r_hat", np.nan),
                         ess_bulk=r.get("ess_bulk", np.nan), divergences=r["divergences"], n_trials=r["n_trials"], seconds=r["seconds"], **(extra or {})))
    df = pd.DataFrame(rows)
    show = df[df.param.str.contains("scaffold|instruction|Intercept|has_code|sigma|z_")].copy()
    print(f"\n=== [{stage}] {label}  ({int(df.n_trials.iloc[0])} trials, {df.seconds.iloc[0]:.0f}s, {int(df.divergences.iloc[0])} divergences, max r_hat {df.r_hat.max():.3f})")
    print(show[["param", "true", "mean", "sd", "hdi3", "hdi97", "covered"]].to_string(index=False, float_format=lambda x: f"{x:7.3f}"))
    return df


# ---------------------------------------------------------------- stages
def stage_param(a, rng, S):
    out = []
    for lab, truth in [("drift-only scaffold (+0.15 v)", truth_table("drift")), ("boundary-only scaffold (+0.5 a)", truth_table("boundary"))]:
        df = simulate(a.n_questions, a.epochs, truth, rng)
        s = fit(pipeline(df), *S)
        out.append(record("param", lab, s, expected(truth)))
        if lab.startswith("drift"):   # plan 6.1 as written (no has_code): what does omitting the covariate do?
            s2 = fit(pipeline(df), *S, with_code=False)
            out.append(record("param", lab + " | fit WITHOUT has_code", s2, expected(truth, with_code=False)))
    return pd.concat(out)


def stage_repeats(a, rng, S):
    out = []; truth = truth_table("drift")
    for reps in (5, 10, 20):
        df = simulate(a.n_questions, reps, truth, rng)
        out.append(record("repeats", f"{reps} repeats x {a.n_questions} questions", fit(pipeline(df), *S), expected(truth), {"reps": reps}))
    return pd.concat(out)


def stage_scaling(a, rng, S):
    truth = truth_table("drift"); k = 1.5
    df = simulate(a.n_questions, a.epochs, truth, rng)
    df["rt"] = df["rt"] * k
    return record("scaling", f"durations x{k}, choices kept: expect v/sqrt(k), a*sqrt(k), t*k", fit(pipeline(df, C=C_STUDY * k), *S), expected(truth, k=k))


def stage_censoring(a, rng, S):
    truth = truth_table("drift"); out = []
    df = simulate(a.n_questions, a.epochs, truth, rng)
    C = float(df[df.outcome == "answered"].rt.quantile(0.85))      # ~15% censored
    print(f"\ncensoring check: C = {C:.2f} time units ({(df[df.outcome=='answered'].rt > C).mean():.1%} of answered runs censored)")
    out.append(record("censoring", f"uncensored reference", fit(pipeline(df), *S), expected(truth), {"C": C}))
    out.append(record("censoring", f"censored at C={C:.1f}, censored rows DROPPED (wrong)", fit(pipeline(df, C=C, censor_mode="drop"), *S), expected(truth), {"C": C}))
    try:
        s = fit(pipeline(df, C=C), *S, deadline=True)
        out.append(record("censoring", f"censored at C={C:.1f}, deadline likelihood P(T>C) (ddm_censoring.py)", s, expected(truth), {"C": C}))
    except Exception as e:
        print(f"\n!! HSSM deadline fit failed: {type(e).__name__}: {str(e)[:400]}")
        out.append(pd.DataFrame([dict(stage="censoring", fit="HSSM deadline likelihood FAILED", param="error", true=np.nan, mean=np.nan, C=C, note=str(e)[:200])]))
    return pd.concat(out)


def stage_bias(a, rng, S):
    truth = truth_table("drift")
    df = simulate(a.n_questions, a.epochs, truth, rng)
    s = fit(pipeline(df), *S, option_coding=True)
    exp = {"z_Intercept": np.log(Z_BIAS / (1 - Z_BIAS)), "v_stim": BASE["v"], "v_stim:has_code": CODE["v"], "v_stim:scaffold[sbs]": 0.15,
           "a_Intercept": np.log(BASE["a"]), "t_Intercept": np.log(BASE["t"]), "a_has_code": np.log(CODE["a"]), "t_has_code": np.log(CODE["t"]),
           "a_instruction[thorough]": 0.5 * np.log(K_THOROUGH), "t_instruction[thorough]": np.log(K_THOROUGH)}   # z on logit scale
    return record("bias", f"option coding, z free: expect z={Z_BIAS}", s, exp)


def gen_fixed_budget(n_q, reps, rng):
    """No accumulation: each condition has a fixed length (lognormal around a condition budget, independent of
    difficulty); correctness is a per-question coin with no length dependence. No scaffold effect on accuracy."""
    budget = {"plain_concise": 2.0, "plain_thorough": 3.0, "sbs_concise": 2.5, "sbs_thorough": 3.5}
    pq = np.clip(rng.beta(5, 1.6, n_q), 0.5, 1.0); has_code = rng.random(n_q) < P_CODE; rows = []
    for q in range(n_q):
        for c in COND:
            for r in range(reps):
                rt = budget[c] * (3.0 if has_code[q] else 1.0) * np.exp(rng.normal(0, 0.15))
                rows.append(dict(qid=f"q{q:03d}", condition=c, scaffold=c.split("_")[0], instruction=c.split("_")[1], rep=r,
                                 correct_is_A=(r % 2 == 0), has_code=bool(has_code[q]), rt=rt, correct=bool(rng.random() < pq[q]), outcome="answered"))
    df = pd.DataFrame(rows); df["response"] = np.where(df.correct, 1, -1); df["chosen"] = "A"; return df


def gen_answer_flip(n_q, reps, rng, p_flip=0.2):
    """Correct accumulation, then the reported option is flipped on 20% of trials (accumulate right, output wrong)."""
    df = simulate(n_q, reps, truth_table("none"), rng, p_zero=0.0)
    flip = rng.random(len(df)) < p_flip
    df.loc[flip, "correct"] = ~df.loc[flip, "correct"]; df["response"] = np.where(df.correct, 1, -1); return df


def gen_lognormal_logistic(n_q, reps, rng):
    """The phase-7 baseline as a generator: log rt ~ N(mu_q + mu_c, s); P(correct) = logit(b_q + beta*log rt). No scaffold effect."""
    mu_q = rng.normal(0, 0.3, n_q); b_q = rng.normal(1.6, 0.9, n_q); has_code = rng.random(n_q) < P_CODE
    mu_c = {"plain_concise": 0.6, "plain_thorough": 1.0, "sbs_concise": 0.8, "sbs_thorough": 1.1}; rows = []
    for q in range(n_q):
        for c in COND:
            for r in range(reps):
                lrt = mu_q[q] + mu_c[c] + (1.1 if has_code[q] else 0) + rng.normal(0, 0.45)
                p = 1 / (1 + np.exp(-(b_q[q] - 0.6 * (lrt - 1.2) - (0.8 if has_code[q] else 0))))
                rows.append(dict(qid=f"q{q:03d}", condition=c, scaffold=c.split("_")[0], instruction=c.split("_")[1], rep=r,
                                 correct_is_A=(r % 2 == 0), has_code=bool(has_code[q]), rt=float(np.exp(lrt)), correct=bool(rng.random() < p), outcome="answered"))
    df = pd.DataFrame(rows); df["response"] = np.where(df.correct, 1, -1); df["chosen"] = "A"; return df


def stage_model(a, rng, S):
    """4.3: fit the DDM to non-DDM data. No generator has a scaffold effect, so any v_scaffold / a_scaffold
    interval excluding 0 is a spurious condition effect. Model comparison itself is phase 7 (07_baseline_cv.py)."""
    out = []
    for lab, gen in [("fixed budget (no accumulation)", gen_fixed_budget), ("answer flip 20% after correct accumulation", gen_answer_flip),
                     ("lognormal length + logistic correctness", gen_lognormal_logistic)]:
        df = gen(a.n_questions, a.epochs, rng)
        d = pipeline(df)
        print(f"\n[{lab}] acc={d.correct.mean():.2f} median rt={d.rt.median():.2f} | acc by condition: " + ", ".join(f"{c} {d[d.condition==c].correct.mean():.2f}" for c in COND))
        s = fit(d, *S)
        exp = {k: 0.0 for k in s.index if "scaffold" in k}        # truth: no scaffold effect anywhere
        out.append(record("model", f"DDM fit to: {lab}", s, exp))
        (OUT / f"model_{gen.__name__}.csv").write_text(df.to_csv(index=False))   # keep the data for 07's comparison
    # positive control for 07: data the DDM did generate (drift-only scaffold truth), same size
    simulate(a.n_questions, a.epochs, truth_table("drift"), rng).to_csv(OUT / "model_gen_ddm_truth.csv", index=False)
    return pd.concat(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["param", "repeats", "scaling", "censoring", "bias", "model", "all"])
    ap.add_argument("--n-questions", type=int, default=50)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--quick", action="store_true", help="400 draws / 500 tune / 2 chains")
    a = ap.parse_args()
    S = (400, 500, 2) if a.quick else (cfg["hssm"]["draws"], cfg["hssm"]["tune"], cfg["hssm"]["chains"])
    rng = np.random.default_rng(SEED)
    stages = {"param": stage_param, "repeats": stage_repeats, "scaling": stage_scaling, "censoring": stage_censoring, "bias": stage_bias, "model": stage_model}
    todo = list(stages) if a.stage == "all" else [a.stage]
    t0 = time.time()
    for st in todo:
        print(f"\n################ stage {st}  ({time.strftime('%H:%M:%S')})")
        res = stages[st](a, rng, S)
        res.to_csv(OUT / f"{st}.csv", index=False)
    with open(OUT / "REPORT.md", "a") as f:
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M')} stages={todo} n_questions={a.n_questions} epochs={a.epochs} draws/tune/chains={S} runtime={(time.time()-t0)/60:.1f} min\n"
                f"Truth: BASE={BASE} CODE={CODE} K_THOROUGH={K_THOROUGH} SD_Q={SD_Q} P_ZERO={P_ZERO} Z_BIAS={Z_BIAS}. Per-stage tables in results/recovery/<stage>.csv.\n")
    print(f"\ndone in {(time.time()-t0)/60:.1f} min -> {OUT}")
