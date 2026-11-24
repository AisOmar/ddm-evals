"""Design check for the task-type-stratified follow-up (2026-10-12).

Design under test: N_c compute questions + N_r recall questions x 4 conditions x 2 repeats
at a 32,768-token cap, option order counterbalanced as in scripts/design.py. The compute
stratum is the population of interest; the recall stratum is a cheap contrast.

Generators (population parameters from the task-type fits on the augmented R1 data):
  two_process_fit   two-process posterior means (augmented_task_all_two_process)
  two_process_weak  same, slow-mode accuracy slope at the weak end of its interval (-0.5)
  two_process_flat  same, slow-mode accuracy independent of length (slope 0)
  baseline_fit      lognormal+logistic, means over the five augmented_task fold posteriors
Candidates fitted with the pre-registered pipeline (08_robustness.py): baseline and
two_process in grouped three-fold CV; ddm_sdv_lapse optionally on selected datasets.

Pre-registered quantities on the compute stratum (all computed here):
  * held-out ELPD differences (joint / length / correctness given length) restricted to
    compute questions, question-level SE, 2-SE rule, diagnostic flags;
  * accuracy of finished compute runs beyond 12,000 tokens, with a question cluster
    bootstrap SE, against each fitted model's posterior-predictive prediction;
  * the within-question log2-length accuracy slope on compute questions (accuracy_fit).

usage: .venv/bin/python scripts/19_stratified_power.py --stage predictions|driver|task|ddm|summarize
No model API calls.
"""
import argparse, importlib.util, json, os, pathlib, subprocess, sys, time
import numpy as np, pandas as pd, scipy.special as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from design import correct_is_a

OUT = ROOT / "results/stratified"
ROB = ROOT / "results/robustness/posteriors"
CONDITIONS = ["plain_concise", "plain_thorough", "sbs_concise", "sbs_thorough"]
CAP = 327.68                    # 32,768 tokens in units of 100
LONG = 120.                     # 12,000 tokens: the pre-registered threshold
BINS = [(0, 120, "0_12k"), (120, 160, "12_16k"), (160, 200, "16_20k"), (200, 245.76, "20_25k"), (245.76, 327.68, "25_33k")]
GENERATORS = ["two_process_fit", "two_process_weak", "two_process_flat", "baseline_fit"]
WEAK_SLOPE, FLAT_SLOPE = -0.5, 0.0
DESIGNS = [(100, 50), (200, 50)]     # (compute, recall) questions
SEEDS = [1, 2]
MODELS = ["baseline", "two_process"]
PRICE = {"deepinfra_fp4": 2.15, "upper": 2.50}   # $ per million output tokens


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _robustness():
    r = _load("robustness", ROOT / "scripts/08_robustness.py"); r.OUT = OUT
    (OUT / "posteriors").mkdir(parents=True, exist_ok=True)
    return r


def _vec(series):
    """Parse an arviz summary mean series into {name: float | array}."""
    out = {}
    for k, v in series.items():
        base = k.split("[")[0]
        if "[" in k: out.setdefault(base, []).append((int(k.split("[")[1].rstrip("]")), v))
        else: out[base] = float(v)
    return {k: (np.array([x for _, x in sorted(v)]) if isinstance(v, list) else v) for k, v in out.items()}


def load_params():
    tp = _vec(pd.read_csv(ROB / "augmented_task_all_two_process_summary.csv", index_col=0)["mean"])
    tp = {k: v for k, v in tp.items() if not k.startswith(("u_f", "b_f", "class_prob"))}
    parts = [pd.read_csv(ROB / f"augmented_task_fold{k}_baseline_summary.csv", index_col=0)["mean"] for k in range(5)]
    m = pd.concat(parts, axis=1).mean(axis=1); m = m[~m.index.str.match(r"^(u|b)\[")]
    bl = _vec(m)
    two = _load("two_process17", ROOT / "scripts/17_two_process.py")
    aug = two.augmented(task=True); centre = float(np.log(aug.rt[~aug.censored]).mean())
    params = dict(two_process=tp, baseline=bl, centre=centre)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "generator_parameters.json").write_text(json.dumps(params, indent=2, default=lambda o: o.tolist()))
    return params


def design(nc, nr, seed):
    rows = []
    for q in range(nc + nr):
        compute = int(q < nc); qid = f"{'c' if compute else 'r'}{q:04d}"
        for ci, condition in enumerate(CONDITIONS):
            s = int(condition.startswith("sbs")); i = int(condition.endswith("thorough"))
            for rep in range(2):
                rows.append(dict(qid=qid, q=q, condition=condition, scaffold="step_by_step" if s else "plain",
                                 instruction="thorough" if i else "concise", rep=rep,
                                 correct_is_A=correct_is_a(qid, condition, rep, CONDITIONS, seed),
                                 has_code=compute, task_type="compute" if compute else "recall", ci=ci, s=s, i=i))
    return pd.DataFrame(rows)


def X_of(d):
    return np.column_stack([np.ones(len(d)), d.s, d.i, d.s * d.i, d.has_code]).astype(float)


def simulate_two_process(d, P, rng, slope=None):
    """Latent lengths (units) and correctness under the two-process model with population parameters P."""
    X = X_of(d); code = d.has_code.to_numpy(); ci = d.ci.to_numpy(); q = d.q.to_numpy(); nq = q.max() + 1
    code_q = np.zeros(nq); code_q[q] = code
    z = rng.random(nq) < sp.expit(P["omega_coefs"][0] + P["omega_coefs"][1] * code_q)
    u_f = rng.normal(0, P["tau_f"], nq); b_f = rng.normal(0, P["tau_bf"], nq)
    p_slow = np.where(z[q], sp.expit(X @ P["pi_coefs"]), sp.expit(P["pi_floor"]))
    slow = rng.random(len(d)) < p_slow
    lrt = np.where(slow, rng.normal(P["mu_s"] + P["gamma_s"] * code, P["sigma_s"]),
                   rng.normal(P["alpha_f"][ci] + P["gamma_f"] * code + u_f[q], P["sigma_f"][ci]))
    beta_s_len = P["beta_s_len"] if slope is None else slope
    eta = np.where(slow, P["beta_s"] + beta_s_len * (lrt - np.log(160)), P["beta_f"][ci] + P["gacc_f"] * code + b_f[q])
    correct = rng.random(len(d)) < sp.expit(eta)
    return np.exp(lrt), correct, slow, z[q]


def simulate_baseline(d, P, centre, rng):
    code = d.has_code.to_numpy(); ci = d.ci.to_numpy(); q = d.q.to_numpy(); nq = q.max() + 1
    u = rng.normal(0, P["tau_u"], nq)[q]; b = rng.normal(0, P["tau_b"], nq)[q]
    lrt = P["alpha"][ci] + P["gamma_len"] * code + u + rng.normal(0, P["sigma"][ci])
    eta = P["beta"][ci] + P["gamma_acc"] * code + b + P["beta_len"] * (lrt - centre)
    return np.exp(lrt), rng.random(len(d)) < sp.expit(eta)


def generate(generator, nc, nr, seed, params, cap=CAP):
    rng = np.random.default_rng(1_000_000 * nc + 1_000 * nr + seed)
    d = design(nc, nr, seed)
    slow = prone = np.full(len(d), np.nan)
    if generator.startswith("two_process"):
        slope = {"two_process_fit": None, "two_process_weak": WEAK_SLOPE, "two_process_flat": FLAT_SLOPE}[generator]
        rt, correct, slow, prone = simulate_two_process(d, params["two_process"], rng, slope)
    elif generator == "baseline_fit":
        rt, correct = simulate_baseline(d, params["baseline"], params["centre"], rng)
    else: raise ValueError(generator)
    cens = rt > cap
    out = d.drop(columns=["q", "s", "i"]).copy()
    out["true_rt"] = rt; out["slow_mode"] = slow; out["slow_prone"] = prone
    out["correct"] = np.where(cens, np.nan, correct.astype(float)); out["response"] = np.where(correct, 1, -1)
    out["rt"] = np.where(cens, cap, rt); out["dl"] = np.where(cens, cap, np.nan); out["censored"] = cens
    out["reasoning_tokens"] = np.round(out.rt * 100).astype(int); out["outcome"] = np.where(cens, "censored", "answered")
    out["provider"] = "simulation"; out["phase"] = "followup"
    return out


def stratum_stats(d, cap=CAP):
    """Model-free compute-stratum quantities with question cluster-bootstrap SEs."""
    c = d[d.has_code == 1]; ans = c[~c.censored]; long = ans.true_rt > LONG
    rng = np.random.default_rng(0); qids = c.qid.unique()
    al = ans[long]; n_q = al.groupby("qid").size().reindex(qids, fill_value=0).to_numpy(); k_q = al.groupby("qid").correct.sum().reindex(qids, fill_value=0).to_numpy()
    pick = rng.integers(len(qids), size=(1000, len(qids)))
    boots = k_q[pick].sum(1) / np.maximum(n_q[pick].sum(1), 1)
    row = dict(n_compute_questions=len(qids), compute_censored=c.censored.mean(), compute_runs_beyond_12k=(c.true_rt > LONG).mean(),
               acc_beyond_12k=k_q.sum() / max(n_q.sum(), 1), acc_beyond_12k_se=float(boots.std(ddof=1)), n_beyond_12k=int(long.sum()),
               acc_upto_12k=ans[~long].correct.mean(), acc_answered=ans.correct.mean(),
               mean_tokens_compute=100 * np.minimum(c.true_rt, cap).mean(), mean_tokens_recall=100 * np.minimum(d[d.has_code == 0].true_rt, cap).mean(),
               recall_censored=d[d.has_code == 0].censored.mean(), recall_acc=d[(d.has_code == 0) & ~d.censored].correct.mean())
    for lo, hi, name in BINS:
        m = (ans.true_rt > lo) & (ans.true_rt <= hi); row[f"acc_{name}"] = ans[m].correct.mean() if m.sum() >= 5 else np.nan
        row[f"n_{name}"] = int(m.sum())
    # within-question contrast: questions with both a short and a long finished repeat
    g = ans.assign(long=long).groupby("qid")
    pairs = [(x[~x.long].correct.mean(), x[x.long].correct.mean()) for _, x in g if x.long.any() and (~x.long).any()]
    row["questions_with_short_and_long"] = len(pairs)
    row["within_question_acc_short_minus_long"] = float(np.mean([a - b for a, b in pairs])) if pairs else np.nan
    return row


def cost(d, cap=CAP):
    tokens = (100 * np.minimum(d.true_rt, cap)).sum() + 40 * len(d)
    return {f"usd_{k}": tokens / 1e6 * p for k, p in PRICE.items()} | dict(output_tokens_m=tokens / 1e6, calls=len(d))


# ---------------------------------------------------------------- model predictions for the pre-registered statistic
def posterior(label):
    import arviz as az
    post = az.extract(az.from_netcdf(ROB / f"{label}.nc"), num_samples=400, random_seed=0)
    return {k: post[k].values for k in post.data_vars if k not in ("u", "b", "u_v", "u_f", "b_f", "class_prob")}


def predictions(n_draws=60, nc=300, seed=0):
    """What each fitted task-type model predicts for the compute stratum at 32,768 tokens: new questions,
    population draws from the fitted posteriors (two_process: full-data fit; baseline, DDM: the five folds pooled)."""
    r = _robustness(); rng = np.random.default_rng(seed); rows = []
    two = _load("two_process17", ROOT / "scripts/17_two_process.py"); aug = two.augmented(task=True); centre = float(np.log(aug.rt[~aug.censored]).mean())
    sim12 = _load("power12", ROOT / "scripts/12_power_simulation.py")
    d = design(nc, 0, seed); X = X_of(d); code = d.has_code.to_numpy(); ci = d.ci.to_numpy(); q = d.q.to_numpy()
    def stats(rt, correct, model, draw):
        cens = rt > CAP; ans = ~cens; long = rt > LONG
        row = dict(model=model, draw=draw, censored=cens.mean(), beyond_12k=(long & ans).mean(), acc_beyond_12k=correct[ans & long].mean() if (ans & long).sum() >= 5 else np.nan,
                   acc_upto_12k=correct[ans & ~long].mean(), acc_answered=correct[ans].mean(), mean_tokens=100 * np.minimum(rt, CAP).mean(), median_tokens=100 * np.median(rt[ans]))
        for lo, hi, name in BINS:
            m = ans & (rt > lo) & (rt <= hi); row[f"acc_{name}"] = correct[m].mean() if m.sum() >= 5 else np.nan
        return row
    P = posterior("augmented_task_all_two_process"); S = P["alpha_f"].shape[-1]
    for k, s in enumerate(rng.integers(S, size=n_draws)):
        Ps = {key: v[..., s] for key, v in P.items()}
        rt, correct, *_ = simulate_two_process(d, Ps, rng); rows.append(stats(rt, correct, "two_process", k))
    folds = [posterior(f"augmented_task_fold{f}_baseline") for f in range(5)]
    for k in range(n_draws):
        P = folds[k % 5]; s = rng.integers(P["alpha"].shape[-1]); Ps = {key: v[..., s] for key, v in P.items()}
        rt, correct = simulate_baseline(d, Ps, centre, rng); rows.append(stats(rt, correct, "baseline", k))
    folds = [posterior(f"augmented_task_fold{f}_ddm_sdv_lapse") for f in range(5)]
    for k in range(n_draws):
        P = folds[k % 5]; s = rng.integers(P["tau_v"].shape[-1]); Ps = {key: v[..., s] for key, v in P.items()}
        u_v = rng.normal(0, Ps["tau_v"], nc)[q]
        v = X @ Ps["v_coefs"] + u_v; a = np.exp(X @ Ps["a_coefs"]); t = np.exp(X @ Ps["t_coefs"])
        sv = np.exp(Ps["sv_coefs"][0] + code * Ps["sv_coefs"][1])
        rt, resp = sim12.sim_ddm(rng.normal(v, sv), a, t, rng, CAP)
        contam = rng.random(len(d)) < Ps["epsilon"]
        rt[contam] = np.exp(rng.normal(np.log(20), 2, contam.sum())); resp[contam] = rng.choice([-1, 1], contam.sum())
        rt = np.where(np.isnan(rt), CAP + 1, rt); rows.append(stats(rt, resp > 0, "ddm_sdv_lapse", k))
    t = pd.DataFrame(rows); t.to_csv(OUT / "model_predictions_draws.csv", index=False)
    summary = t.drop(columns="draw").groupby("model").agg(["mean", lambda x: x.quantile(.05), lambda x: x.quantile(.95)])
    summary.columns = [f"{a}_{ {'mean': 'mean', '<lambda_0>': 'q05', '<lambda_1>': 'q95'}[b] }" for a, b in summary.columns]
    summary.to_csv(OUT / "model_predictions.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 60)
    print(summary.round(3).T.to_string()); return summary


# ---------------------------------------------------------------- fitting
def label_of(g, nc, nr, s): return f"strat_{g}_c{nc}_r{nr}_s{s}"


def budgets(args):
    hi = argparse.Namespace(draws=args.draws, tune=args.tune, chains=4, target_accept=.99, dense_mass=False)
    ddm = argparse.Namespace(draws=1000, tune=1000, chains=4, target_accept=.95, dense_mass=False)
    return hi, ddm


def run_task(generator, nc, nr, seed, args, models=MODELS):
    r = _robustness(); params = load_params(); hi, ddm = budgets(args)
    label = label_of(generator, nc, nr, seed); path = OUT / f"{label}.csv"
    if path.exists(): d = pd.read_csv(path)
    else: d = generate(generator, nc, nr, seed, params); d.to_csv(path, index=False)
    start = time.time()
    cheap = [m for m in models if m != "ddm_sdv_lapse"]
    if cheap: r.cv(d, label, cheap, hi, k=3)
    if "ddm_sdv_lapse" in models: r.cv(d, label, ["ddm_sdv_lapse"], ddm, k=3)
    slope_path = OUT / f"{label}_slope.json"
    if cheap and not slope_path.exists():
        c = d[d.has_code == 1].copy(); c["has_code"] = 0      # constant covariate within the stratum
        res = r.accuracy_fit(c, f"{label}_compute_slope", hi); slope_path.write_text(json.dumps(res, indent=2))
    print(f"{label} done in {time.time()-start:.0f}s", flush=True)


def tasks_list():
    out = []
    for nc, nr in sorted(DESIGNS, reverse=True):
        for s in SEEDS:
            for g in GENERATORS:
                if g in ("two_process_weak", "two_process_flat") and nc != max(DESIGNS)[0]: continue
                out.append((g, nc, nr, s))
    return out


def driver(workers, args, stage="task", labels=None):
    tasks = tasks_list() if labels is None else labels
    env = dict(os.environ, XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=4",
               OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4", MKL_NUM_THREADS="4")
    (OUT / "logs").mkdir(parents=True, exist_ok=True); running = []
    def launch(task):
        g, nc, nr, s = task; label = label_of(g, nc, nr, s)
        done = (OUT / f"{label}_slope.json").exists() if stage == "task" else all((OUT / f"{label}_fold{k}_ddm_sdv_lapse_scores.csv").exists() for k in range(3))
        if done: return None
        log = open(OUT / "logs" / f"{label}{'_ddm' if stage == 'ddm' else ''}.log", "a")
        cmd = [sys.executable, __file__, "--stage", stage, "--generator", g, "--compute", str(nc), "--recall", str(nr), "--seed", str(s),
               "--draws", str(args.draws), "--tune", str(args.tune)]
        print(f"launch {label} [{stage}]", flush=True)
        return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=ROOT)
    while tasks or running:
        running = [p for p in running if p.poll() is None]
        while tasks and len(running) < workers:
            p = launch(tasks.pop(0))
            if p is not None: running.append(p)
        time.sleep(20)
    print("driver finished", flush=True)


# ---------------------------------------------------------------- summary
def flagged(info): return bool(info["divergences"] or info["max_rhat"] > 1.05 or info["min_ess"] < 50)


def summarize():
    r = _robustness(); params = load_params(); rng = np.random.default_rng(0)
    # population truth per generator (large simulation)
    truth = []
    for g in GENERATORS:
        d = generate(g, 4000, 1000, 77, params); truth.append(dict(generator=g, **stratum_stats(d)))
    truth = pd.DataFrame(truth).drop(columns=["acc_beyond_12k_se", "n_compute_questions"]); truth.to_csv(OUT / "truth.csv", index=False)
    rows = []; stats = []; diag = []; costs = []
    for g, nc, nr, s in tasks_list():
        label = label_of(g, nc, nr, s); per = OUT / f"{label}_cv_per_trial.csv"
        if not per.exists(): continue
        d = pd.read_csv(OUT / f"{label}.csv"); frame = pd.read_csv(per)
        if not all(f"lpd_{m}_joint" in frame for m in MODELS): continue
        models = list(MODELS)
        ddm_parts = [OUT / f"{label}_fold{k}_ddm_sdv_lapse_scores.csv" for k in range(3)]
        if all(p.exists() for p in ddm_parts):
            dd = pd.concat([pd.read_csv(p) for p in ddm_parts])
            frame = frame.merge(dd[["qid", "condition", "rep"] + [f"lpd_ddm_sdv_lapse_{c}" for c in r.COMPONENTS]], on=["qid", "condition", "rep"], validate="one_to_one")
            models.append("ddm_sdv_lapse")
        infos = {}
        for k in range(3):
            for m in models:
                p = OUT / "posteriors" / f"{label}_fold{k}_{m}_diagnostics.json"
                if p.exists():
                    i = json.loads(p.read_text()); infos[(k, m)] = i
                    diag.append(dict(label=label, generator=g, compute=nc, recall=nr, seed=s, fold=k, model=m, minutes=i["seconds"] / 60, divergences=i["divergences"], max_rhat=i["max_rhat"], min_ess=i["min_ess"], flagged=flagged(i)))
        for cand, ref in [("two_process", "baseline"), ("two_process", "ddm_sdv_lapse"), ("ddm_sdv_lapse", "baseline")]:
            if cand not in models or ref not in models: continue
            flag = any(flagged(i) for (k, m), i in infos.items() if m in (cand, ref))
            for subset, fr in [("all", frame), ("compute", frame[frame.has_code == 1]), ("recall", frame[frame.has_code == 0])]:
                t = r.comparison(fr, cand, ref); t["z"] = t.elpd / t.se
                t["score_verdict"] = t.verdict.replace({"candidate better": f"{cand} better", "baseline better": f"{ref} better"})
                t["verdict"] = np.where(flag, "unreliable fit; no verdict", t.score_verdict)
                t["generator"] = g; t["compute"] = nc; t["recall"] = nr; t["seed"] = s; t["subset"] = subset; t["label"] = label
                rows.append(t)
        st = stratum_stats(d); slope = json.loads((OUT / f"{label}_slope.json").read_text()) if (OUT / f"{label}_slope.json").exists() else {}
        tr = truth[truth.generator == g].iloc[0]
        stats.append(dict(generator=g, compute=nc, recall=nr, seed=s, **st, true_acc_beyond_12k=tr.acc_beyond_12k, true_acc_upto_12k=tr.acc_upto_12k,
                          slope_log2=slope.get("log_odds_per_doubling"), slope_lo=slope.get("lo"), slope_hi=slope.get("hi"), slope_p_negative=slope.get("probability_negative"),
                          slope_excludes_zero=(slope.get("hi", 1) < 0) if slope else None, errors_compute=slope.get("errors")))
        costs.append(dict(generator=g, compute=nc, recall=nr, seed=s, **cost(d)))
    res = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(); res.to_csv(OUT / "power_results.csv", index=False)
    st = pd.DataFrame(stats); st.to_csv(OUT / "stratum_statistics.csv", index=False)
    pd.DataFrame(diag).to_csv(OUT / "fit_diagnostics.csv", index=False); co = pd.DataFrame(costs); co.to_csv(OUT / "costs.csv", index=False)
    pred = pd.read_csv(OUT / "model_predictions.csv", index_col=0) if (OUT / "model_predictions.csv").exists() else None
    write_report(res, st, truth, pd.DataFrame(diag), co, pred)


def fmt(x, nd=2): return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:,.{nd}f}"


def write_report(res, st, truth, diag, co, pred):
    L = ["# Stratified follow-up: design check", "",
         f"Generated {pd.Timestamp.today():%Y-%m-%d} by `scripts/19_stratified_power.py`. Design: N_c compute + N_r recall questions x 4 conditions x 2 repeats at 32,768 tokens, option order counterbalanced. Generators use the task-type fits on the augmented R1 data (`results/robustness/posteriors/augmented_task_*`). Candidates are fitted with `08_robustness.py` (grouped 3-fold CV by question, question-level SE, 2-SE rule, flags: any divergence, r-hat > 1.05, bulk ESS < 50). No API calls.", ""]
    if pred is not None:
        L += ["## What the three fitted models predict for the compute stratum at 32,768 tokens", "",
              "New compute questions, population draws from the task-type posteriors (two_process: full augmented fit; baseline and DDM: the five fold posteriors pooled). Mean and 90% interval over draws. This is the pre-registered prediction table: the follow-up measures these quantities on the compute stratum.", "",
              "| Quantity | two_process | baseline | ddm_sdv_lapse |", "| --- | ---: | ---: | ---: |"]
        for qn in ["censored", "beyond_12k", "acc_upto_12k", "acc_beyond_12k", "acc_12_16k", "acc_16_20k", "acc_20_25k", "acc_25_33k", "acc_answered", "median_tokens", "mean_tokens"]:
            if f"{qn}_mean" not in pred.columns: continue
            cells = [f"{pred.loc[m, f'{qn}_mean']:.3g} ({pred.loc[m, f'{qn}_q05']:.3g} to {pred.loc[m, f'{qn}_q95']:.3g})" if m in pred.index else "n/a" for m in ["two_process", "baseline", "ddm_sdv_lapse"]]
            L.append(f"| {qn} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["## Generator truth (compute stratum, 4,000-question simulation)", "", "| Generator | Censored at 32k | Runs beyond 12k | Accuracy up to 12k | Accuracy beyond 12k | 12-16k | 16-20k | 20-25k | 25-33k | Within-question short minus long | Mean tokens compute | Mean tokens recall |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for _, x in truth.iterrows():
        L.append(f"| {x.generator} | {x.compute_censored:.3f} | {x.compute_runs_beyond_12k:.2f} | {x.acc_upto_12k:.3f} | {x.acc_beyond_12k:.3f} | {fmt(x.acc_12_16k)} | {fmt(x.acc_16_20k)} | {fmt(x.acc_20_25k)} | {fmt(x.acc_25_33k)} | {fmt(x.within_question_acc_short_minus_long)} | {x.mean_tokens_compute:,.0f} | {x.mean_tokens_recall:,.0f} |")
    if len(co):
        L += ["", "## Cost per simulated dataset", "", "| Generator | Compute q | Recall q | Calls | Output tokens (M) | USD at $2.15/M | USD at $2.50/M |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for _, x in co.groupby(["generator", "compute", "recall"], as_index=False).mean(numeric_only=True).iterrows():
            L.append(f"| {x.generator} | {x.compute:.0f} | {x.recall:.0f} | {x.calls:,.0f} | {x.output_tokens_m:.1f} | {x.usd_deepinfra_fp4:,.0f} | {x.usd_upper:,.0f} |")
    if len(st):
        L += ["", "## Pre-registered compute-stratum statistics on each simulated dataset", "",
              "Accuracy beyond 12,000 tokens with a question cluster-bootstrap SE against the generator's population value; within-question log2-length slope (log-odds per doubling, 95% interval) from `accuracy_fit` on compute questions.", "",
              "| Generator | Compute q | Seed | Runs beyond 12k | n beyond 12k | Accuracy beyond 12k (SE) | Truth | Accuracy up to 12k | Questions with short and long | Within-q short minus long | Slope per doubling (95%) | Excludes 0 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
        for _, x in st.iterrows():
            L.append(f"| {x.generator} | {x.compute} | {x.seed} | {x.compute_runs_beyond_12k:.2f} | {x.n_beyond_12k} | {x.acc_beyond_12k:.3f} ({x.acc_beyond_12k_se:.3f}) | {x.true_acc_beyond_12k:.3f} | {x.acc_upto_12k:.3f} | {x.questions_with_short_and_long} | {fmt(x.within_question_acc_short_minus_long)} | {fmt(x.slope_log2)} ({fmt(x.slope_lo)} to {fmt(x.slope_hi)}) | {x.slope_excludes_zero} |")
    if len(res):
        L += ["", "## Held-out model comparison", "", "ELPD differences (positive favours the first-named model), question-level SE, and the verdict under the pre-registered rule. `compute` rows score only the compute questions of the held-out folds.", "",
              "| Generator | Compute q | Seed | Subset | Comparison | Component | ELPD | SE | z | Verdict |", "| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | --- |"]
        for _, x in res[res.subset != "recall"].iterrows():
            L.append(f"| {x.generator} | {x.compute} | {x.seed} | {x.subset} | {x.model} | {x.component} | {x.elpd:,.1f} | {x.se:,.1f} | {x.z:.1f} | {x.verdict} |")
        j = res[(res.subset == "compute") & (res.component == "joint") & (res.model == "two_process - baseline")]
        L += ["", "Compute-stratum joint verdicts, two_process against baseline: " + "; ".join(f"{g}: {', '.join(v)}" for g, v in j.groupby('generator').verdict.agg(list).items()) + "."]
    if len(diag):
        fl = diag[diag.flagged]
        L += ["", "## Diagnostics", "", f"{len(diag)} fits, {len(fl)} flagged; mean minutes per fit by model: " + ", ".join(f"{m} {v:.1f}" for m, v in diag.groupby('model').minutes.mean().items()) + "."]
        if len(fl): L.append("Flagged: " + "; ".join(f"{x.label} fold {x.fold} {x.model} (div {x.divergences}, r-hat {x.max_rhat:.2f}, ESS {x.min_ess:.0f})" for _, x in fl.iterrows()) + ".")
    L += ["", "Files: `model_predictions.csv`, `truth.csv`, `stratum_statistics.csv`, `power_results.csv`, `fit_diagnostics.csv`, `costs.csv`, per-dataset `strat_*.csv` with per-trial scores and posteriors under this directory."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n"); print("wrote", OUT / "REPORT.md")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["predictions", "driver", "task", "ddm", "ddm_driver", "summarize"], required=True)
    ap.add_argument("--generator", choices=GENERATORS); ap.add_argument("--compute", type=int); ap.add_argument("--recall", type=int, default=50); ap.add_argument("--seed", type=int)
    ap.add_argument("--draws", type=int, default=1500); ap.add_argument("--tune", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=3); ap.add_argument("--out")
    ap.add_argument("--ddm-labels", nargs="*", help="generator:compute:recall:seed entries for the DDM stage")
    args = ap.parse_args()
    if args.out: OUT = pathlib.Path(args.out)
    OUT.mkdir(parents=True, exist_ok=True)
    if args.stage == "predictions": predictions()
    elif args.stage == "driver": driver(args.workers, args)
    elif args.stage == "task": run_task(args.generator, args.compute, args.recall, args.seed, args)
    elif args.stage == "ddm": run_task(args.generator, args.compute, args.recall, args.seed, args, models=["ddm_sdv_lapse"])
    elif args.stage == "ddm_driver":
        labels = [tuple(int(v) if i else v for i, v in enumerate(x.split(":"))) for x in args.ddm_labels]
        driver(args.workers, args, stage="ddm", labels=labels)
    elif args.stage == "summarize": summarize()
