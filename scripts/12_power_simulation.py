"""Realistic design power check for the proposed follow-up study. No API calls.

Question: at the proposed design (N questions x 4 conditions x 2 repeats, one
pinned upstream, 32,768-token cap), can grouped-by-question CV with the
question-level 2-SE rule tell a drift-variability DDM from the lognormal +
logistic baseline, when the data look like R1 rather than like a textbook DDM?

Generators (all 100-token time units, cap 327.68):
  sdv_fit      ddm_sdv + contaminant at the population posterior means of the
               five R1 fold fits (results/robustness/posteriors/main_fold*_ddm_sdv_lapse).
               Question drift effects, per-run drift variability and the
               contaminant are all drawn as the fitted model specifies.
  baseline_fit lognormal length + logistic correctness at the posterior means of
               the five R1 baseline fold fits.
  mixture      neither model: a fast fixed-drift DDM with a question- and
               code-dependent probability of entering a slow lognormal mode whose
               accuracy falls with length (the cap-experiment pattern).
Fits reuse 08_robustness.py (same likelihoods, priors, sampler settings, CV
and comparison code) with outputs redirected to results/power.

usage: .venv/bin/python scripts/12_power_simulation.py --stage calibrate
       .venv/bin/python scripts/12_power_simulation.py --stage driver --workers 4
       .venv/bin/python scripts/12_power_simulation.py --stage task --generator sdv_fit --questions 400 --seed 1
       .venv/bin/python scripts/12_power_simulation.py --stage summarize
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ddm-mpl")
os.environ.setdefault("JAX_ENABLE_X64", "true")
os.environ.setdefault("PYTENSOR_FLAGS", "base_compiledir=/tmp/ddm-pytensor,mode=FAST_RUN")
import argparse, importlib.util, json, pathlib, subprocess, sys, time
import numpy as np, pandas as pd, scipy.special as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from design import correct_is_a

OUT = ROOT / "results/power"
OUT.mkdir(exist_ok=True); (OUT / "posteriors").mkdir(exist_ok=True); (OUT / "logs").mkdir(exist_ok=True)
CONDITIONS = ["plain_concise", "plain_thorough", "sbs_concise", "sbs_thorough"]
CAP = 327.68            # 32,768 tokens
STEP1_CAP = 81.92       # 8,192 tokens, for calibration against the step-1 data
CODE_SHARE = 0.44       # 22 of the 50 step-1 questions contain code
GENERATORS = ["sdv_fit", "baseline_fit", "mixture"]
SIZES = [100, 400]
SEEDS = [1, 2, 3]
ROB = ROOT / "results/robustness/posteriors"


def _robustness():
    spec = importlib.util.spec_from_file_location("robustness", ROOT / "scripts/08_robustness.py")
    r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
    r.OUT = OUT
    return r


def fold_means(name):
    """Population parameters averaged over the five R1 fold posteriors (means)."""
    parts = [pd.read_csv(ROB / f"main_fold{k}_{name}_summary.csv", index_col=0)["mean"] for k in range(5)]
    m = pd.concat(parts, axis=1).mean(axis=1)
    m = m[~m.index.str.match(r"^(u|b|u_v)\[")]
    def vec(prefix):
        keys = sorted([k for k in m.index if k.startswith(prefix + "[")], key=lambda s: int(s.split("[")[1][:-1]))
        return np.array([m[k] for k in keys])
    if name == "ddm_sdv_lapse":
        return dict(v_coefs=vec("v_coefs"), a_coefs=vec("a_coefs"), t_coefs=vec("t_coefs"),
                    sv_coefs=vec("sv_coefs"), tau_v=float(m["tau_v"]), epsilon=float(m["epsilon"]))
    return dict(alpha=vec("alpha"), sigma=vec("sigma"), gamma_len=float(m["gamma_len"]), tau_u=float(m["tau_u"]),
                beta=vec("beta"), gamma_acc=float(m["gamma_acc"]), beta_len=float(m["beta_len"]), tau_b=float(m["tau_b"]))


def r1_centre():
    d = pd.read_csv(ROOT / "results/robustness/pilot_r1_with_provider.csv")
    ok = (d.outcome == "answered") & (d.reasoning_tokens <= 8192) & (d.reasoning_tokens > 0)
    return float(np.log(d.loc[ok, "reasoning_tokens"] / 100).mean())


def design(n_questions, seed, rng):
    rows = []
    for q in range(n_questions):
        code = int(rng.random() < CODE_SHARE)
        for ci, condition in enumerate(CONDITIONS):
            s = int(condition.startswith("sbs")); i = int(condition.endswith("thorough"))
            for rep in range(2):
                rows.append(dict(qid=f"q{q:04d}", q=q, condition=condition, scaffold="step_by_step" if s else "plain",
                                 instruction="thorough" if i else "concise", rep=rep,
                                 correct_is_A=correct_is_a(f"q{q:04d}", condition, rep, CONDITIONS, seed),
                                 has_code=code, ci=ci, s=s, i=i))
    return pd.DataFrame(rows)


def X_of(d):
    return np.column_stack([np.ones(len(d)), d.s, d.i, d.s * d.i, d.has_code]).astype(float)


def sim_ddm(v, a, t, rng, cap=CAP, dt=0.01):
    """Euler simulation of a symmetric DDM (boundaries +/-a, start 0, noise 1).
    Returns total time t + decision time (nan if still running at the cap) and response (+1 upper)."""
    n = len(v); x = np.zeros(n); alive = np.ones(n, bool); rt = np.full(n, np.nan); resp = np.zeros(n)
    sq = np.sqrt(dt); steps = int(np.ceil(cap / dt)) + 1
    for k in range(1, steps + 1):
        idx = np.flatnonzero(alive)
        if not len(idx): break
        x[idx] += v[idx] * dt + sq * rng.standard_normal(len(idx))
        up = x[idx] >= a[idx]; dn = x[idx] <= -a[idx]; done = up | dn
        if done.any():
            d = idx[done]; rt[d] = t[d] + k * dt; resp[d] = np.where(up[done], 1, -1); alive[d] = False
    return rt, resp


def generate(generator, n_questions, seed, params, cap=CAP):
    rng = np.random.default_rng(10_000 * n_questions + seed)
    d = design(n_questions, seed, rng); X = X_of(d); code = d.has_code.to_numpy(); nq = n_questions; q = d.q.to_numpy()
    if generator == "sdv_fit":
        P = params["sdv"]
        u_v = rng.normal(0, P["tau_v"], nq)[q]
        v = X @ P["v_coefs"] + u_v; a = np.exp(X @ P["a_coefs"]); t = np.exp(X @ P["t_coefs"])
        sv = np.exp(P["sv_coefs"][0] + code * P["sv_coefs"][1])
        rt, resp = sim_ddm(rng.normal(v, sv), a, t, rng, cap)
        contam = rng.random(len(d)) < P["epsilon"]
        rt[contam] = np.exp(rng.normal(np.log(20), 2, contam.sum())); resp[contam] = rng.choice([-1, 1], contam.sum())
        correct = resp > 0
    elif generator == "baseline_fit":
        P = params["baseline"]; ci = d.ci.to_numpy()
        u = rng.normal(0, P["tau_u"], nq)[q]; b = rng.normal(0, P["tau_b"], nq)[q]
        lrt = P["alpha"][ci] + P["gamma_len"] * code + u + rng.normal(0, P["sigma"][ci])
        eta = P["beta"][ci] + P["gamma_acc"] * code + b + P["beta_len"] * (lrt - params["centre"])
        rt = np.exp(lrt); correct = rng.random(len(d)) < sp.expit(eta)
    elif generator == "mixture":
        # Fast accurate accumulation, plus a slow mode whose accuracy falls with length.
        ua = rng.normal(0, 0.4, nq)[q]; upi = rng.normal(0, 0.8, nq)[q]
        # fast mode: ~97-99% accurate, medians ~600 (prose) / ~2,600 (code) tokens, mostly non-decision time
        v = np.where(code == 1, 0.6, 0.9); a = np.where(code == 1, 4., 2.) * np.exp(ua + 0.1 * d.i.to_numpy())
        rt, resp = sim_ddm(v, a, np.where(code == 1, 20., 4.) * np.exp(0.15 * d.i.to_numpy()), rng, cap)
        slow = rng.random(len(d)) < sp.expit(sp.logit(0.22) + 1.7 * code + upi)
        n_slow = slow.sum()
        lrt_slow = rng.normal(np.log(160) + 0.3 * code[slow] + 0.18 * d.i.to_numpy()[slow], 0.45)
        rt[slow] = np.exp(lrt_slow)
        resp[slow] = np.where(rng.random(n_slow) < sp.expit(1.2 - 1.5 * (lrt_slow - np.log(160))), 1, -1)
        correct = resp > 0
    else:
        raise ValueError(generator)
    cens = np.isnan(rt) | (rt > cap)
    out = d.drop(columns=["q", "s", "i"]).copy()
    out["true_rt"] = rt
    out["correct"] = np.where(cens, np.nan, correct.astype(float))
    out["response"] = np.where(correct, 1, -1)
    out["rt"] = np.where(cens, cap, rt); out["dl"] = np.where(cens, cap, np.nan); out["censored"] = cens
    out["provider"] = "simulation"; out["outcome"] = np.where(cens, "censored", "answered")
    return out


def load_params():
    p = dict(sdv=fold_means("ddm_sdv_lapse"), baseline=fold_means("baseline"), centre=r1_centre())
    (OUT / "generator_parameters.json").write_text(json.dumps({k: ({kk: (vv.tolist() if hasattr(vv, "tolist") else vv) for kk, vv in v.items()} if isinstance(v, dict) else v) for k, v in p.items()}, indent=2))
    return p


def profile(d, cap):
    """Summary statistics comparable to the step-1 and cap-experiment tables."""
    c = d.censored | (d.true_rt.isna()) | (d.true_rt > cap)
    ans = d[~c]
    row = dict(censored=c.mean(), censored_prose=c[d.has_code == 0].mean(), censored_code=c[d.has_code == 1].mean(),
               acc_answered=ans.correct.mean(), median_prose_tokens=100 * ans[ans.has_code == 0].true_rt.median(),
               median_code_tokens=100 * ans[ans.has_code == 1].true_rt.median(),
               p90_tokens=100 * ans.true_rt.quantile(.9))
    # accuracy by finish length, as in fig6
    bins = [0, 40, 81.92, 120, 160, 200, 327.68]
    acc = ans.groupby(pd.cut(ans.true_rt, bins), observed=True).correct.agg(["mean", "size"])
    row.update({f"acc_{int(b.left*100/1000)}k_{int(b.right*100/1000)}k": f"{m:.2f} (n={n})" for b, (m, n) in acc.iterrows()})
    return row


def calibrate(params):
    rows = []
    r1 = pd.read_csv(ROOT / "results/robustness/pilot_r1_with_provider.csv")
    for g in GENERATORS:
        d = generate(g, 400, 99, params)
        for cap, label in [(STEP1_CAP, "8,192"), (CAP, "32,768")]:
            rows.append(dict(generator=g, cap=label, **profile(d, cap)))
    t = pd.DataFrame(rows); t.to_csv(OUT / "generator_calibration.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("R1 step 1 at 8,192 (post-hoc cap): censored 0.43 (prose 0.26, code 0.64); answered accuracy 0.96; "
          "answered medians prose 890 / code 4,900 tokens.\nCap experiment at 24,576 on twice-stuck cells: 81% finish, "
          "76% of finishers correct, accuracy 1.00 (<12k) -> 0.80 -> 0.67 -> 0.60 (20-24.6k).\n")
    print(t.round(3).to_string(index=False))


def run_task(generator, n_questions, seed, draws, tune):
    r = _robustness()
    params = load_params()
    label = f"power_{generator}_q{n_questions}_s{seed}"
    path = OUT / f"{label}.csv"
    if path.exists(): d = pd.read_csv(path)
    else: d = generate(generator, n_questions, seed, params); d.to_csv(path, index=False)
    args = argparse.Namespace(draws=draws, tune=tune, chains=2, target_accept=.95, dense_mass=False)
    start = time.time()
    r.cv(d, label, ["baseline", "ddm_sdv_lapse"], args, k=3)
    print(f"{label} done in {time.time()-start:.0f}s", flush=True)


def driver(workers, draws, tune, sizes, seeds, generators):
    tasks = [(g, n, s) for n in sorted(sizes, reverse=True) for s in seeds for g in generators]
    env = dict(os.environ, XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=3",
               OMP_NUM_THREADS="3", OPENBLAS_NUM_THREADS="3", MKL_NUM_THREADS="3")
    running = []
    def launch(task):
        g, n, s = task; label = f"power_{g}_q{n}_s{s}"
        if (OUT / f"{label}_cv_comparison.csv").exists(): return None
        log = open(OUT / "logs" / f"{label}.log", "a")
        cmd = [sys.executable, __file__, "--stage", "task", "--generator", g, "--questions", str(n), "--seed", str(s),
               "--draws", str(draws), "--tune", str(tune)]
        print(f"launch {label}", flush=True)
        return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
    while tasks or running:
        running = [p for p in running if p.poll() is None]
        while tasks and len(running) < workers:
            p = launch(tasks.pop(0))
            if p is not None: running.append(p)
        time.sleep(20)
    print("driver finished", flush=True)


def flagged(info):
    return bool(info["divergences"] or info["max_rhat"] > 1.05 or info["min_ess"] < 50)


def refine(label, fold, models, draws, tune, chains, target_accept, dense_mass):
    """Refit one fold of one simulated dataset with a larger sampler budget (11_refine_fits settings) under a
    separate label, rescore the held-out fold and print the fold comparison. Original fits are untouched."""
    r = _robustness()
    d = pd.read_csv(OUT / f"{label}.csv")
    ids = np.array(sorted(d.qid.unique())); np.random.default_rng(r.SEED).shuffle(ids)
    held = np.array_split(ids, 3)[fold]; train = d[~d.qid.isin(held)]; test = d[d.qid.isin(held)].copy()
    args = argparse.Namespace(draws=draws, tune=tune, chains=chains, target_accept=target_accept, dense_mass=dense_mass)
    budget = f"refined_d{draws}_t{tune}_c{chains}_a{target_accept}_dense{int(dense_mass)}"
    for name in models:
        tag = f"{label}_fold{fold}_{name}_{budget}"
        start = time.time()
        P = r.fit_model(train, name, tag, args)
        pred = r.predict(P, test, seed=r.SEED + fold + 1)
        for comp, vals in pred.items(): test[f"lpd_{name}_{comp}"] = vals
        print(f"{tag}: {time.time()-start:.0f}s", flush=True)
    test.to_csv(OUT / f"{label}_fold{fold}_{budget}_scores.csv", index=False)
    if set(models) == {"baseline", "ddm_sdv_lapse"}:
        for comp in ["joint", "length", "correctness_given_length"]:
            x = test[f"lpd_ddm_sdv_lapse_{comp}"] - test[f"lpd_baseline_{comp}"]
            print(f"fold {fold} {comp}: DDM - baseline = {x.sum():.1f}, question SE {r.question_se(x, test.qid):.1f}", flush=True)


def summarize():
    """Per-dataset verdicts under the report's rule: a diagnostic failure in any fold means no verdict.
    A secondary comparison over the folds that passed diagnostics is also reported."""
    r = _robustness()
    rows = []; curve = []; folds_rows = []
    rng = np.random.default_rng(0)
    comps = ["joint", "length", "correctness_given_length"]
    for g in GENERATORS:
        for n in SIZES:
            for s_ in SEEDS:
                label = f"power_{g}_q{n}_s{s_}"
                if not (OUT / f"{label}_cv_comparison.csv").exists(): continue
                frame = pd.read_csv(OUT / f"{label}_cv_per_trial.csv"); data = pd.read_csv(OUT / f"{label}.csv")
                fold_ok = {}
                for k in range(3):
                    infos = {m: json.loads((OUT / "posteriors" / f"{label}_fold{k}_{m}_diagnostics.json").read_text()) for m in ["baseline", "ddm_sdv_lapse"]}
                    fold_ok[k] = not any(flagged(i) for i in infos.values())
                    for m, i in infos.items():
                        folds_rows.append(dict(generator=g, questions=n, seed=s_, fold=k, model=m, seconds=i["seconds"], divergences=i["divergences"],
                                               max_rhat=i["max_rhat"], min_ess=i["min_ess"], flagged=flagged(i)))
                n_valid = sum(fold_ok.values()); valid = frame[frame.fold.map(fold_ok)]
                for comp in comps:
                    x = frame[f"lpd_ddm_sdv_lapse_{comp}"] - frame[f"lpd_baseline_{comp}"]
                    total = float(x.sum()); se = r.question_se(x, frame.qid); z = total / se
                    score_verdict = "DDM better" if z > 2 else "baseline better" if z < -2 else "inconclusive"
                    xv = valid[f"lpd_ddm_sdv_lapse_{comp}"] - valid[f"lpd_baseline_{comp}"]
                    tv = float(xv.sum()); sev = r.question_se(xv, valid.qid) if len(valid) else np.nan; zv = tv / sev if len(valid) else np.nan
                    valid_verdict = ("DDM better" if zv > 2 else "baseline better" if zv < -2 else "inconclusive") if len(valid) else "none"
                    verdict = score_verdict if n_valid == 3 else f"fit failure ({3-n_valid}/3 folds); no verdict"
                    rows.append(dict(generator=g, questions=n, seed=s_, component=comp, elpd=total, se=se, z=z, score_verdict=score_verdict,
                                     verdict=verdict, valid_folds=n_valid, elpd_valid=tv, se_valid=sev, z_valid=zv, valid_verdict=valid_verdict,
                                     n_trials_valid=len(valid), censored=data.censored.mean(), acc_answered=data.correct.mean(),
                                     fit_seconds=sum(fr["seconds"] for fr in folds_rows if fr["generator"] == g and fr["questions"] == n and fr["seed"] == s_)))
                if n == max(SIZES) and len(valid):
                    x = valid["lpd_ddm_sdv_lapse_joint"] - valid["lpd_baseline_joint"]
                    dq = x.groupby(valid.qid).sum().to_numpy()
                    for m in [50, 100, 150, 200, 300, 400]:
                        if m > len(dq): continue
                        if m == len(dq): zs = np.array([dq.sum() / np.sqrt(len(dq) * dq.var(ddof=1))])
                        else:
                            sub = np.stack([rng.choice(dq, m, replace=False) for _ in range(4000)])
                            zs = sub.sum(1) / np.sqrt(m * sub.var(1, ddof=1))
                        curve.append(dict(generator=g, seed=s_, valid_folds=n_valid, questions_available=len(dq), questions=m, mean_z=zs.mean(),
                                          p_ddm_better=(zs > 2).mean(), p_baseline_better=(zs < -2).mean(), p_inconclusive=((zs >= -2) & (zs <= 2)).mean()))
    res = pd.DataFrame(rows); res.to_csv(OUT / "power_results.csv", index=False)
    pd.DataFrame(folds_rows).to_csv(OUT / "fit_diagnostics.csv", index=False)
    cur = pd.DataFrame(curve); cur.to_csv(OUT / "power_curve_subsampled.csv", index=False)
    j = res[res.component == "joint"].copy()
    truth = {"sdv_fit": "DDM better", "baseline_fit": "baseline better", "mixture": None}
    def agg(d):
        t = truth[d.name[0]]
        fail = d.verdict.str.startswith("fit failure")
        out = dict(datasets=len(d), fit_failures=int(fail.sum()),
                   ddm_better=int((d.verdict == "DDM better").sum()), baseline_better=int((d.verdict == "baseline better").sum()),
                   inconclusive=int((d.verdict == "inconclusive").sum()),
                   correct_decisive=int((d.verdict == t).sum()) if t else np.nan,
                   wrong_decisive=int(((d.verdict.isin(["DDM better", "baseline better"])) & (d.verdict != t)).sum()) if t else np.nan,
                   valid_folds_ddm_better=int((d.valid_verdict == "DDM better").sum()), valid_folds_baseline_better=int((d.valid_verdict == "baseline better").sum()),
                   mean_z_valid=d.z_valid.mean(), min_z_valid=d.z_valid.min(), max_z_valid=d.z_valid.max(),
                   censored=d.censored.mean(), acc_answered=d.acc_answered.mean(), fit_hours=d.fit_seconds.sum() / 3600)
        return pd.Series(out)
    summary = j.groupby(["generator", "questions"]).apply(agg, include_groups=False).reset_index()
    summary.to_csv(OUT / "power_summary.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(summary.round(3).to_string(index=False)); print()
    if len(cur):
        print(cur.groupby(["generator", "questions"])[["mean_z", "p_ddm_better", "p_baseline_better", "p_inconclusive"]].mean().round(3).to_string())
    print(); print(j[["generator", "questions", "seed", "elpd", "se", "z", "verdict", "valid_folds", "z_valid", "valid_verdict", "censored", "acc_answered"]].round(2).to_string(index=False))
    write_report(summary, j, cur, pd.DataFrame(folds_rows))


def refit_table():
    """One row per heavy-budget refit (posteriors/*_refined_*_diagnostics.json), with the rescored fold difference when both models of that fold were refitted."""
    import re
    rows = []
    for f in sorted((OUT / "posteriors").glob("*_refined_*_diagnostics.json")):
        info = json.loads(f.read_text())
        m = re.match(r"power_(?P<dataset>.+)_fold(?P<fold>\d)_(?P<model>baseline|ddm_sdv_lapse)_refined_(?P<budget>d\d+_t\d+_c\d+_a[\d.]+_dense[01])", f.stem.replace("_diagnostics", ""))
        if not m:
            continue
        g = m.groupdict(); fold = int(g["fold"])
        refit_diff = refit_se = default_diff = float("nan")
        sc = OUT / f"power_{g['dataset']}_fold{fold}_refined_{g['budget']}_scores.csv"
        if sc.exists():
            r = pd.read_csv(sc); d = r.lpd_ddm_sdv_lapse_joint - r.lpd_baseline_joint
            refit_diff = d.sum(); refit_se = _robustness().question_se(d.values, r.qid.values)
        b = OUT / f"power_{g['dataset']}_fold{fold}_baseline_scores.csv"; dm = OUT / f"power_{g['dataset']}_fold{fold}_ddm_sdv_lapse_scores.csv"
        if b.exists() and dm.exists():
            default_diff = (pd.read_csv(dm).lpd_ddm_sdv_lapse_joint.values - pd.read_csv(b).lpd_baseline_joint.values).sum()
        rows.append(dict(dataset=g["dataset"], fold=fold, model=g["model"], draws=info["draws"], chains=info["chains"], tune=info["tune"], dense_mass=bool(info.get("dense_mass", False)),
                         minutes=info["seconds"] / 60, divergences=info["divergences"], max_rhat=info["max_rhat"], min_ess=info["min_ess"], passes=not flagged(info),
                         refit_diff=refit_diff, refit_se=refit_se, default_diff=default_diff))
    t = pd.DataFrame(rows)
    if len(t):
        t.to_csv(OUT / "refits.csv", index=False)
    return t


def write_report(summary, j, cur, diag):
    cal = pd.read_csv(OUT / "generator_calibration.csv")
    L = ["# Design power check for the proposed follow-up (simulation, no API calls)", "",
         f"Generated {pd.Timestamp.today():%Y-%m-%d} by `scripts/12_power_simulation.py --stage summarize`. Fitting, CV, question-level SE and the 2-SE rule are those of `08_robustness.py`; sampler budget 2 chains x 400 draws after 500 tuning steps, grouped three-fold CV.", "",
         "## Generators", "",
         "| Generator | What is true | Source of parameters |", "| --- | --- | --- |",
         "| sdv_fit | drift-variability DDM + 6% contaminant | posterior means of the five R1 fold fits of `ddm_sdv_lapse` (`generator_parameters.json`) |",
         "| baseline_fit | lognormal length + logistic correctness | posterior means of the five R1 fold fits of `baseline` |",
         "| mixture | neither: fast fixed-drift DDM, plus a slow lognormal mode (P = 22% prose / 60% code, question-varying) whose accuracy falls with length | hand-set to the step-1 and cap-experiment tables |", "",
         "Calibration against the data (R1 step 1 at 8,192: 43% censored, prose 26% / code 64%; answered accuracy 0.96; medians 890 / 4,900 tokens):", "",
         "| Generator | Cap | Censored | Prose | Code | Answered accuracy | Median prose tokens | Median code tokens |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for _, c in cal.iterrows():
        L.append(f"| {c.generator} | {c.cap} | {c.censored:.2f} | {c.censored_prose:.2f} | {c.censored_code:.2f} | {c.acc_answered:.2f} | {c.median_prose_tokens:,.0f} | {c.median_code_tokens:,.0f} |")
    L += ["", "## Verdicts per dataset (joint held-out-question ELPD, DDM minus baseline)", "",
          "A dataset gets a verdict only if all three folds pass diagnostics for both models (no divergences, r-hat <= 1.05, bulk ESS >= 50); otherwise it is a fit failure. The valid-fold columns rescore the folds that passed.", "",
          "| Generator | Questions | Seed | ELPD | SE | z | Verdict | Valid folds | z (valid folds) | Verdict (valid folds) | Censored | Accuracy |",
          "| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: |"]
    for _, x in j.iterrows():
        L.append(f"| {x.generator} | {x.questions} | {x.seed} | {x.elpd:,.0f} | {x.se:,.0f} | {x.z:.1f} | {x.verdict} | {x.valid_folds}/3 | {x.z_valid:.1f} | {x.valid_verdict} | {x.censored:.2f} | {x.acc_answered:.2f} |")
    L += ["", "## Summary", "", "| Generator | Questions | Datasets | Fit failures | DDM better | Baseline better | Inconclusive | Mean z (valid folds) | Fit hours |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for _, x in summary.iterrows():
        L.append(f"| {x.generator} | {x.questions} | {x.datasets} | {x.fit_failures} | {x.ddm_better} | {x.baseline_better} | {x.inconclusive} | {x.mean_z_valid:.1f} | {x.fit_hours:.1f} |")
    if len(cur):
        L += ["", "## Power against question count (subsampled from the 400-question datasets)", "",
              "Question-level differences from the scored 400-question datasets are resampled without replacement; the fits used two thirds of 400 questions, so this understates the loss of training data at small sizes. Direct 100-question fits are in the tables above.", "",
              "| Generator | Questions | Mean z | P(DDM better) | P(baseline better) | P(inconclusive) |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for (g, m), x in cur.groupby(["generator", "questions"])[["mean_z", "p_ddm_better", "p_baseline_better", "p_inconclusive"]].mean().iterrows():
            L.append(f"| {g} | {m} | {x.mean_z:.1f} | {x.p_ddm_better:.2f} | {x.p_baseline_better:.2f} | {x.p_inconclusive:.2f} |")
    ref = refit_table()
    if len(ref):
        L += ["", "## Heavy-budget refits of flagged folds", "",
              "Single folds refitted with `--stage refine` (longer tuning, more chains, higher target acceptance); the fold difference is rescored on the same held-out questions. The default-budget column is the same fold scored from the flagged fits.", "",
              "| Dataset | Fold | Model | Draws x chains (tune) | Dense mass | Minutes | Divergences | r-hat | ESS | Diagnostics | Fold ELPD diff (refit) | SE | Fold ELPD diff (default) |",
              "| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |"]
        for _, x in ref.iterrows():
            L.append(f"| {x.dataset} | {x.fold} | {x.model} | {x.draws} x {x.chains} ({x.tune}) | {x.dense_mass} | {x.minutes:.0f} | {x.divergences} | {x.max_rhat:.3f} | {x.min_ess:.0f} | {'pass' if x.passes else 'FLAG'} | {x.refit_diff if pd.isna(x.refit_diff) else f'{x.refit_diff:,.1f}'} | {x.refit_se if pd.isna(x.refit_se) else f'{x.refit_se:,.1f}'} | {x.default_diff if pd.isna(x.default_diff) else f'{x.default_diff:,.1f}'} |")
    fl = diag[diag.flagged]
    L += ["", "## Fit diagnostics", "", f"{len(diag)} fits; {len(fl)} flagged. Flagged fits: " + ("; ".join(f"{x.generator} q{x.questions} s{x.seed} fold{x.fold} {x.model} (div {x.divergences}, r-hat {x.max_rhat:.2f}, ESS {x.min_ess:.0f})" for _, x in fl.iterrows()) if len(fl) else "none") + ".",
          "", "Files: `power_results.csv` (all components), `power_summary.csv`, `power_curve_subsampled.csv`, `fit_diagnostics.csv`, `generator_calibration.csv`, `generator_parameters.json`, per-dataset `power_*_cv_per_trial.csv` and posteriors."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n")
    print(f"wrote {OUT/'REPORT.md'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["calibrate", "driver", "task", "summarize", "refine"], required=True)
    ap.add_argument("--label"); ap.add_argument("--fold", type=int, default=0); ap.add_argument("--models", nargs="+", default=["baseline", "ddm_sdv_lapse"])
    ap.add_argument("--chains", type=int, default=4); ap.add_argument("--target-accept", type=float, default=.995); ap.add_argument("--dense-mass", action="store_true")
    ap.add_argument("--generator", choices=GENERATORS); ap.add_argument("--questions", type=int); ap.add_argument("--seed", type=int)
    ap.add_argument("--draws", type=int, default=400); ap.add_argument("--tune", type=int, default=500)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--sizes", type=int, nargs="+", default=SIZES); ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    ap.add_argument("--generators", nargs="+", default=GENERATORS)
    a = ap.parse_args()
    if a.stage == "calibrate": calibrate(load_params())
    elif a.stage == "task": run_task(a.generator, a.questions, a.seed, a.draws, a.tune)
    elif a.stage == "driver": driver(a.workers, a.draws, a.tune, a.sizes, a.seeds, a.generators)
    elif a.stage == "refine": refine(a.label, a.fold, a.models, a.draws, a.tune, a.chains, a.target_accept, a.dense_mass)
    else: summarize()
