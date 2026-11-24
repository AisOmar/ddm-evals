"""Offline report corrections and checkpointed Bayesian sensitivity analyses.

No API calls. Existing raw/CV artifacts are preserved. Run from the repo root:
  .venv/bin/python scripts/08_robustness.py --stage prepare
  .venv/bin/python scripts/08_robustness.py --stage fits
  .venv/bin/python scripts/08_robustness.py --stage recovery
  .venv/bin/python scripts/08_robustness.py --stage summarize
The default uses 2 chains, 400 draws, 500 tuning iterations and grouped 5-fold
CV for the main comparison (3-fold for sensitivity/recovery comparisons).
All new analyses are exploratory. Posterior files, diagnostics and per-trial
scores are saved, with completed folds reused on restart.
"""
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/ddm-mpl")
os.environ.setdefault("JAX_ENABLE_X64", "true")
os.environ.setdefault("PYTENSOR_FLAGS", "base_compiledir=/tmp/ddm-pytensor,mode=FAST_RUN")
import argparse
import importlib.util
import json
import pathlib
import time
import warnings
import fcntl
import re
import numpy as np
import pandas as pd
import scipy.special as sp
from scipy.stats import norm
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from diffusion_likelihood import log_density, log_survival, evaluate
from design import correct_is_a

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "results/robustness"
OUT.mkdir(exist_ok=True)
(OUT / "posteriors").mkdir(exist_ok=True)
CONDITIONS = ["plain_concise", "plain_thorough", "sbs_concise", "sbs_thorough"]
SEED = 20261006
COMPONENTS = ["joint", "length", "correctness_given_length"]


def normal_logsf(z):
    """Finite gradients even in the remote Normal tail under JAX."""
    central=pt.log(pt.erfc(pt.minimum(z,8.)/np.sqrt(2)))-np.log(2)
    high=pt.maximum(z,8.)
    correction=1-1/high**2+3/high**4-15/high**6+105/high**8
    tail=-.5*high**2-.5*np.log(2*np.pi)-pt.log(high)+pt.log(correction)
    return pt.switch(z>8.,tail,central)


def question_se(x, qids):
    totals = pd.Series(np.asarray(x)).groupby(np.asarray(qids)).sum()
    return float(np.sqrt(len(totals)*totals.var(ddof=1))) if len(totals)>1 else np.nan


def comparison(frame, candidate="ddm", reference="baseline", target="held-out questions"):
    rows = []
    for c in COMPONENTS:
        x = frame[f"lpd_{candidate}_{c}"] - frame[f"lpd_{reference}_{c}"]
        total, se = float(x.sum()), question_se(x, frame.qid)
        verdict = "candidate better" if total>2*se else "baseline better" if total< -2*se else "inconclusive"
        rows.append(dict(target=target, component=c, model=f"{candidate} - {reference}", elpd=total, se=se,
                         per_trial=total/len(x), n=len(x), n_questions=frame.qid.nunique(), se_unit="question", verdict=verdict))
    return pd.DataFrame(rows)


def prepare():
    from inspect_ai.log import read_eval_log
    # Provider provenance from raw responses, never inferred from outcomes.
    providers = []
    for phase in ["pilot_r1", "cap_experiment"]:
        for path in (ROOT/"logs"/phase).glob("*.eval"):
            log = read_eval_log(str(path))
            for sample in log.samples or []:
                provider = "unrecorded"
                for event in sample.events:
                    if getattr(event, "event", None)=="model" and event.call:
                        response = event.call.response
                        if isinstance(response, dict):
                            provider = response.get("provider", provider)
                providers.append(dict(phase=phase, sample_id=sample.id, provider=provider))
    provenance = pd.DataFrame(providers)
    provenance.to_csv(OUT/"providers.csv", index=False)
    for phase in ["pilot_r1", "cap_experiment"]:
        frame = pd.read_csv(ROOT/f"results/{phase}.csv")
        frame = frame.merge(provenance[provenance.phase==phase], on="sample_id", validate="one_to_one")
        frame.to_csv(OUT/f"{phase}_with_provider.csv", index=False)
    # Recalculate every available comparison; never rewrite historical scores.
    corrected = []
    for path in sorted((ROOT/"results").glob("cv_*_per_trial.csv")):
        frame = pd.read_csv(path)
        table = comparison(frame); table["dataset"] = path.stem.removesuffix("_per_trial")
        corrected.append(table)
    pd.concat(corrected).to_csv(OUT/"historical_question_uncertainty.csv", index=False)
    old=pd.read_csv(ROOT/"results/cv_pilot_r1_per_trial.csv")
    floor=(~old.censored)&(old.lpd_ddm_joint< -65)
    difference=old.lpd_ddm_joint-old.lpd_baseline_joint
    loss=[]
    for label,mask in [("censored",old.censored),("density_floor",floor),("remaining_answered",(~old.censored)&(~floor))]:
        loss.append(dict(group=label,n=int(mask.sum()),elpd=float(difference[mask].sum()),se=question_se(difference.where(mask,0),old.qid)))
    pd.DataFrame(loss).to_csv(OUT/"historical_r1_loss_components.csv",index=False)
    from scipy.optimize import brentq
    accuracy=.96;k=.5*sp.logit(accuracy);median=50.;deadline=81.92
    survival=lambda C,a:float(np.exp(evaluate(C,0,k/a,a,0.,censored=True,nodes=128)))
    root=brentq(lambda a:(1-survival(median,a))-.5*(1-survival(deadline,a)),.1,30.)
    pd.DataFrame([dict(accuracy=accuracy,median_tokens=median*100,cap_tokens=deadline*100,t=0,a=root,v=k/root,
                       censoring=survival(deadline,root))]).to_csv(OUT/"conditional_median_tail.csv",index=False)
    # Old secondary files lack per-trial scores. Their clustered SE cannot be
    # recovered from an aggregate CSV; rerun the fits in the fits stage.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r1 = pd.read_csv(ROOT/"results/pilot_r1.csv")
    cap = pd.read_csv(ROOT/"results/cap_experiment.csv")
    groups = [(r1[(r1.outcome=="answered")&(r1.reasoning_tokens<=8192)], [0,1000,2000,4000,8192], ["≤1k","1–2k","2–4k","4–8.2k"]),
              (cap[cap.outcome=="answered"], [0,12000,16000,20000,24576], ["≤12k","12–16k","16–20k","20–24.6k"])]
    fig, axes = plt.subplots(1,2, figsize=(11,4.5), sharey=True)
    figure_rows = []
    for ax, (frame, bins, labels), phase in zip(axes, groups, ["Step 1: completed by the 8,192 cap", "Cap experiment: selected slow cells"]):
        grouped = frame.groupby(pd.cut(frame.reasoning_tokens,bins),observed=True).correct.agg(["sum","size"])
        p = grouped["sum"].astype(float)/grouped["size"]
        n = grouped["size"].to_numpy(); z=1.96; denom=1+z*z/n
        centre=(p+z*z/(2*n))/denom; half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
        ax.bar(range(len(p)),p,color="#2a78d6",width=.65)
        ax.errorbar(range(len(p)),p,yerr=np.vstack([p-(centre-half),(centre+half)-p]),fmt="none",color="#555555",capsize=4)
        ax.set_xticks(range(len(p)),labels); ax.set_title(phase,fontsize=10); ax.set_ylim(0,1.12)
        ax.set_xlabel("Reasoning tokens before the answer")
        for j,(rate,count) in enumerate(zip(p,n)): ax.text(j,.035,f"n={count}",ha="center",color="white")
        for label,k,count in zip(labels,grouped["sum"],n): figure_rows.append(dict(phase=phase,bin=label,correct=int(k),n=int(count),accuracy=float(k/count)))
    axes[0].set_ylabel("Accuracy of completed runs (95% Wilson interval)")
    fig.suptitle("R1 accuracy by length: separate data collections",fontweight="bold")
    fig.text(.02,.015,"Step-1 overruns are excluded. Cap-only ≤12k includes one run below 8,192. Bins pool questions; intervals do not adjust for question clustering.",fontsize=8)
    fig.tight_layout(rect=[0,.055,1,.95]);fig.savefig(ROOT/"results/figures_r1/fig6_accuracy_by_length.png",dpi=170);plt.close(fig)
    pd.DataFrame(figure_rows).to_csv(OUT/"figure6_source.csv",index=False)
    print("Prepared provider provenance, historical clustered SE and corrected figure.",flush=True)


def task_type_map():
    """qid -> 'compute' | 'recall' from data/processed/task_type.csv (scripts/18_task_type.py)."""
    return pd.read_csv(ROOT/"data/processed/task_type.csv").set_index("qid").task_type


def data(scenario="main"):
    # A '_task' suffix swaps the has_code covariate for the compute/recall task type
    # (same column name, so every model and matrix() pick it up unchanged).
    task = scenario.endswith("_task"); scenario = scenario.removesuffix("_task")
    raw = pd.read_csv(OUT/"pilot_r1_with_provider.csv")
    if scenario=="exclude_incomplete": raw=raw[raw.outcome!="incomplete"].copy()
    if scenario=="deepinfra": raw=raw[raw.provider=="DeepInfra"].copy()
    d = raw[raw.outcome.isin(["answered","censored","incomplete"])].copy()
    d["censored"] = d.outcome.isin(["censored","incomplete"])
    # Cap enforcement is based on total generation, even for hidden-only timing.
    over = (~d.censored)&(d.reasoning_tokens>8192)
    d.loc[over,"censored"]=True
    d["rt"] = d.reasoning_tokens/100
    d["dl"] = np.where(d.censored,81.92,np.nan)
    inc = d.outcome=="incomplete"
    d.loc[inc,"dl"] = np.minimum(d.loc[inc,"reasoning_tokens"]/100,81.92)
    if scenario=="hidden_only":
        d["rt"] = d.hidden_reasoning_tokens/100
        # By truncation, hidden reasoning is observed up to this count; total
        # generation caps do not imply a common hidden-only deadline.
        d.loc[d.censored,"dl"] = np.minimum(d.loc[d.censored,"hidden_reasoning_tokens"]/100,81.92)
    d.loc[d.censored,"rt"] = d.loc[d.censored,"dl"]
    d["correct"] = d.correct.astype(float)
    d["response"] = np.where(d.correct==1,1,-1)
    d["has_code"] = d.has_code.astype(int)
    if task: d["has_code"] = (d.qid.map(task_type_map())=="compute").astype(int)
    d["ci"] = pd.Categorical(d.condition,categories=CONDITIONS).codes
    return d[d.rt>0].reset_index(drop=True)


def matrix(d, providers=None):
    s = d.scaffold.isin(["step_by_step","sbs"]).astype(float).to_numpy()
    i = (d.instruction=="thorough").astype(float).to_numpy()
    cols = [np.ones(len(d)),s,i,s*i,d.has_code.to_numpy(float)]
    names = ["Intercept","scaffold","instruction","interaction","has_code"]
    for provider in providers or []:
        cols.append((d.provider==provider).astype(float).to_numpy());names.append(f"provider_{provider}")
    return np.column_stack(cols), names


def diagnostics(idata, label, elapsed, settings=None):
    # class_prob (two_process) is a deterministic per-question posterior class
    # probability, often numerically 0 or 1; its ESS is ill-defined and it is not a
    # sampled parameter, so it is reported in the summary but excluded from the flags.
    summary = az.summary(idata,kind="all",ci_prob=.95,ci_kind="hdi")
    sampled = summary[~summary.index.str.startswith("class_prob")]
    summary.to_csv(OUT/"posteriors"/f"{label}_summary.csv")
    info = dict(label=label,seconds=elapsed,divergences=int(idata.sample_stats.diverging.sum()),
                max_rhat=float(sampled.r_hat.max()), min_ess=float(sampled.ess_bulk.min()),
                draws=int(idata.posterior.sizes["draw"]),chains=int(idata.posterior.sizes["chain"]))
    info.update(settings or {})
    (OUT/"posteriors"/f"{label}_diagnostics.json").write_text(json.dumps(info,indent=2))
    print(info,flush=True)
    return info


def sample_model(model, label, args, initvals=None):
    path = OUT/"posteriors"/f"{label}.nc"
    with path.with_suffix(".lock").open("a+") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if path.exists(): return az.from_netcdf(path)
        start=time.time()
        with model:
            chains=getattr(args,"chains",2)
            idata=pm.sample(draws=args.draws,tune=args.tune,chains=chains,cores=chains,
                            random_seed=SEED,progressbar=False,target_accept=getattr(args,"target_accept",.95),
                            nuts_sampler="numpyro", nuts_sampler_kwargs={"chain_method":"vectorized","dense_mass":getattr(args,"dense_mass",False)},
                            initvals=initvals)
        temporary=path.with_suffix(".tmp.nc")
        idata.to_netcdf(temporary);temporary.replace(path)
        diagnostics(idata,label,time.time()-start,dict(tune=args.tune,target_accept=getattr(args,"target_accept",.95),
                                                      dense_mass=getattr(args,"dense_mass",False),random_seed=SEED,
                                                      centered_effects=getattr(args,"centered_effects",False)))
    return idata


def fit_model(train, name, label, args, provider_adjust=False):
    q_codes, qids=pd.factorize(train.qid)
    provider_levels = sorted(train.provider.unique())[1:] if provider_adjust else []
    X, terms=matrix(train,provider_levels); ci=train.ci.to_numpy(); code=train.has_code.to_numpy()
    obs=~train.censored.to_numpy(); rt=train.rt.to_numpy(); y=train.correct.to_numpy(); n_terms=X.shape[1]
    centre=float(np.log(rt[obs]).mean())
    with pm.Model() as model:
        if name=="baseline":
            alpha=pm.Normal("alpha",1,2,shape=4); sigma=pm.HalfNormal("sigma",1,shape=4)
            gamma_len=pm.Normal("gamma_len",0,1.5); tau_u=pm.HalfNormal("tau_u",1)
            if getattr(args,"centered_effects",False):
                u_raw=pm.Normal("u_raw",0,tau_u,shape=len(qids))
                # Keep the standardized posterior variable expected by predict().
                pm.Deterministic("u",u_raw/tau_u);u=u_raw
            else:
                u=pm.Normal("u",0,1,shape=len(qids))*tau_u
            mu=alpha[ci]+gamma_len*code+u[q_codes]
            if provider_adjust:
                plen=pm.Normal("provider_len",0,1,shape=len(provider_levels));mu=mu+X[:,5:]@plen
            pm.Normal("lrt",mu=mu[obs],sigma=sigma[ci[obs]],observed=np.log(rt[obs]))
            cens_idx=np.where(~obs)[0]
            if len(cens_idx):
                # Explicit log survival avoids infinite bounds in JAX gradients.
                standardized=(np.log(rt[cens_idx])-mu[cens_idx])/sigma[ci[cens_idx]]
                pm.Potential("length_survival",normal_logsf(standardized).sum())
            beta=pm.Normal("beta",1,2,shape=4); gamma_acc=pm.Normal("gamma_acc",0,1.5)
            beta_len=pm.Normal("beta_len",0,1.5);tau_b=pm.HalfNormal("tau_b",1.5)
            b=pm.Normal("b",0,1,shape=len(qids))*tau_b
            eta=beta[ci]+gamma_acc*code+b[q_codes]+beta_len*(np.log(rt)-centre)
            if provider_adjust:
                pacc=pm.Normal("provider_acc",0,1,shape=len(provider_levels));eta=eta+X[:,5:]@pacc
            pm.Bernoulli("correct",logit_p=eta[obs],observed=y[obs])
            init=None
        elif name=="two_process":
            # Third candidate (2026-10-12): two-process mixture with a two-class question
            # structure. Each question is slow-prone (class S, probability omega by
            # covariate) or not (class R). On a slow-prone question a trial enters the
            # slow mode with a condition-dependent probability; on other questions with
            # a small floor. Fast mode = lognormal length by condition with a question
            # effect and length-independent accuracy; slow mode = long lognormal length
            # whose accuracy declines in log length. The discrete class replaces a
            # normal question effect on the slow-mode logit, whose posterior SD ran to
            # ~8 and made the sampler bimodal: the data want a two-point distribution.
            # Slow-mode priors are centred on the cap-experiment tables (median finish
            # 15,900 tokens, 76% correct) with broad scales; the slow-mode spread is
            # unidentified when every slow run is censored, hence a lognormal prior.
            nq=len(qids); Q=np.zeros((nq,len(train)));Q[q_codes,np.arange(len(train))]=1.   # question x trial indicator
            code_q=np.array([code[q_codes==k][0] for k in range(nq)],float)
            w=pm.Normal("omega_coefs",0,1.5,shape=2); log_omega=-pt.logaddexp(0.,-(w[0]+w[1]*code_q)); log_1momega=-pt.logaddexp(0.,w[0]+w[1]*code_q)
            pi_coefs=pm.Normal("pi_coefs",mu=np.r_[1.,np.zeros(4)],sigma=1.,shape=5); pi_R=pm.Normal("pi_floor",-4,1.5)
            logit_S=X[:,:5]@pi_coefs; logit_R=pi_R
            alpha_f=pm.Normal("alpha_f",2,1.5,shape=4);gamma_f=pm.Normal("gamma_f",0,1);sigma_f=pm.HalfNormal("sigma_f",.7,shape=4)
            tau_f=pm.HalfNormal("tau_f",1.);u_f=pm.Normal("u_f",0,1,shape=nq)*tau_f
            mu_f=alpha_f[ci]+gamma_f*code+u_f[q_codes]
            mu_s0=pm.Normal("mu_s",np.log(160),.6);gamma_s=pm.Normal("gamma_s",0,.7);sigma_s=pm.LogNormal("sigma_s",np.log(.4),.5)
            mu_s=mu_s0+gamma_s*code
            beta_f=pm.Normal("beta_f",3,1.5,shape=4);gacc_f=pm.Normal("gacc_f",0,1)
            tau_bf=pm.HalfNormal("tau_bf",1.5);b_f=pm.Normal("b_f",0,1,shape=nq)*tau_bf
            eta_f=beta_f[ci]+gacc_f*code+b_f[q_codes]
            beta_s=pm.Normal("beta_s",1.2,1.);beta_s_len=pm.Normal("beta_s_len",-1.5,1.5)
            if provider_adjust:
                plen=pm.Normal("provider_len",0,1,shape=len(provider_levels));mu_f=mu_f+X[:,5:]@plen
                ppi=pm.Normal("provider_slow",0,1,shape=len(provider_levels));logit_S=logit_S+X[:,5:]@ppi
            lrt=np.log(rt);eta_s=beta_s+beta_s_len*(lrt-np.log(160))
            zf=(lrt-mu_f)/sigma_f[ci];zs=(lrt-mu_s)/sigma_s
            # Constants (Jacobian -log rt) omitted in training, included in predict().
            len_f=pt.switch(obs,-.5*zf**2-pt.log(sigma_f[ci])-.5*np.log(2*np.pi),normal_logsf(zf))
            len_s=pt.switch(obs,-.5*zs**2-pt.log(sigma_s)-.5*np.log(2*np.pi),normal_logsf(zs))
            sign=np.where(obs&(y==1),1.,-1.)   # NaN-free constants; censored rows contribute no correctness term
            cor_f=pt.switch(obs,-pt.logaddexp(0.,-sign*eta_f),0.);cor_s=pt.switch(obs,-pt.logaddexp(0.,-sign*eta_s),0.)
            def trial_lp(logit):
                log_p=-pt.logaddexp(0.,-logit);log_1mp=-pt.logaddexp(0.,logit)
                return pt.logaddexp(log_1mp+len_f+cor_f,log_p+len_s+cor_s)
            lpS_q=Q@trial_lp(logit_S); lpR_q=Q@trial_lp(logit_R*pt.ones_like(logit_S))
            aS=log_omega+lpS_q; aR=log_1momega+lpR_q
            pm.Potential("joint_likelihood",pt.logaddexp(aS,aR).sum())
            pm.Deterministic("class_prob",pt.exp(aS-pt.logaddexp(aS,aR)))   # posterior P(slow-prone) per fitted question
            init={"u_f":np.zeros(nq),"b_f":np.zeros(nq)}
        else:
            v_coefs=pm.Normal("v_coefs",mu=np.r_[.4,np.zeros(n_terms-1)],sigma=.6,shape=n_terms)
            a_coefs=pm.Normal("a_coefs",mu=np.r_[np.log(4),np.zeros(n_terms-1)],sigma=.7,shape=n_terms)
            t_coefs=pm.Normal("t_coefs",mu=np.r_[np.log(.5),np.zeros(n_terms-1)],sigma=.8,shape=n_terms)
            tau_v=pm.HalfNormal("tau_v",.5)
            if getattr(args,"centered_effects",False):
                u_v_raw=pm.Normal("u_v_raw",0,tau_v,shape=len(qids))
                pm.Deterministic("u_v",u_v_raw/tau_v);u_v=u_v_raw
            else:
                u_v=pm.Normal("u_v",0,1,shape=len(qids))*tau_v
            v=X@v_coefs+u_v[q_codes]; a=pt.exp(X@a_coefs);t=pt.exp(X@t_coefs)
            if "tq" in name:
                tau_t=pm.HalfNormal("tau_t",.7);u_t=pm.Normal("u_t",0,1,shape=len(qids))*tau_t
                t=pt.exp(X@t_coefs+u_t[q_codes])
            sv=pt.zeros_like(v)
            if "sdv" in name:
                sv_coefs=pm.Normal("sv_coefs",mu=[np.log(.4),0],sigma=.8,shape=2)
                sv=pt.exp(sv_coefs[0]+code*sv_coefs[1])
            lp=pt.zeros_like(v)
            lp=pt.set_subtensor(lp[np.where(obs)[0]],log_density(rt[obs],np.where(y[obs]==1,1,-1),v[obs],a[obs],t[obs],sv[obs]))
            idx=np.where(~obs)[0]
            if len(idx): lp=pt.set_subtensor(lp[idx],log_survival(rt[idx],v[idx],a[idx],t[idx],sv[idx]))
            if "lapse" in name:
                # Proper joint contaminant: broad positive length, fair response.
                # Same density/survival in training and prediction. Unlike a
                # fixed floor it is normalised and penalised by an estimated rate.
                epsilon=pm.Beta("epsilon",1,19)
                contam=np.where(obs,norm.logpdf(np.log(rt),np.log(20),2)-np.log(rt)-np.log(2),norm.logsf((np.log(rt)-np.log(20))/2))
                lp=pt.logaddexp(pt.log1p(-epsilon)+lp,pt.log(epsilon)+contam)
            pm.Potential("joint_likelihood",lp.sum())
            init={"t_coefs":np.r_[np.log(.05),np.zeros(n_terms-1)],
                  "u_v_raw" if getattr(args,"centered_effects",False) else "u_v":np.zeros(len(qids))}
            if "tq" in name: init["u_t"]=np.zeros(len(qids))
    public_init=getattr(args,"initial_hyperparameters",{}).get(name,{})
    if public_init:
        init={**(init or {}),**public_init}
    idata=sample_model(model,label,args,init)
    posterior=az.extract(idata,num_samples=min(400,args.draws*2),random_seed=0)
    P={k:posterior[k].values for k in posterior.data_vars}
    P.update(qids=list(qids),providers=provider_levels,terms=terms,centre=centre,name=name)
    return P


def predict(P, test, own=False, M=40, seed=0, analytic=False):
    if analytic:
        if own or P["providers"] or "tq" in P["name"]:
            raise ValueError("Analytic population prediction only supports unadjusted new-question models.")
        from recovery_marginal import posterior_predict_exact
        return posterior_predict_exact(P,test)
    rng=np.random.default_rng(seed); name=P["name"];X,_=matrix(test,P["providers"])
    n=len(test); S=P["alpha"].shape[-1] if name=="baseline" else P["alpha_f"].shape[-1] if name=="two_process" else P["v_coefs"].shape[-1]
    if own: M=1
    # Share a population draw across rows belonging to the same held-out qid.
    qi,questions=pd.factorize(test.qid)
    def effect(var,tau):
        if own:
            indices=[P["qids"].index(q) for q in test.qid]
            return (P[var][indices]*P[tau])[...,None]
        return (rng.normal(size=(len(questions),S,M))*P[tau][None,:,None])[qi]
    rt=test.rt.to_numpy(); y=test.correct.to_numpy();cens=test.censored.to_numpy();ci=test.ci.to_numpy();code=test.has_code.to_numpy()
    if name=="baseline":
        mu=P["alpha"][ci][...,None]+code[:,None,None]*P["gamma_len"][None,:,None]+effect("u","tau_u")
        eta=P["beta"][ci][...,None]+code[:,None,None]*P["gamma_acc"][None,:,None]+effect("b","tau_b")+P["beta_len"][None,:,None]*(np.log(rt)[:,None,None]-P["centre"])
        if P["providers"]:
            mu+=(X[:,5:]@P["provider_len"])[...,None];eta+=(X[:,5:]@P["provider_acc"])[...,None]
        sd=P["sigma"][ci][...,None];z=(np.log(rt)[:,None,None]-mu)/sd
        length=np.where(cens[:,None,None],norm.logsf(z),norm.logpdf(z)-np.log(sd)-np.log(rt)[:,None,None])
        correct=np.where(y[:,None,None]==1,-np.logaddexp(0,-eta),-np.logaddexp(0,eta))
        joint=length+np.where(cens[:,None,None],0,correct)
    elif name=="two_process":
        lrt=np.log(rt)[:,None,None];cc=code[:,None,None];c3=cens[:,None,None]
        omega=1/(1+np.exp(-(P["omega_coefs"][0][None,:,None]+cc*P["omega_coefs"][1][None,:,None])))   # (n,S,1)
        if own:
            indices=[P["qids"].index(q) for q in test.qid]; pS=P["class_prob"][indices][...,None]
            z=rng.random(size=(n,S,M))<pS
        else:
            z=rng.random(size=(len(questions),S,M))[qi]<omega   # class shared by rows of a question
        logit_S=(X[:,:5]@P["pi_coefs"])[...,None]
        if P["providers"]: logit_S=logit_S+(X[:,5:]@P["provider_slow"])[...,None]
        logit_slow=np.where(z,np.broadcast_to(logit_S,z.shape),P["pi_floor"][None,:,None])
        mu_f=P["alpha_f"][ci][...,None]+cc*P["gamma_f"][None,:,None]+effect("u_f","tau_f");sd_f=P["sigma_f"][ci][...,None]
        mu_s=P["mu_s"][None,:,None]+cc*P["gamma_s"][None,:,None];sd_s=P["sigma_s"][None,:,None]
        if P["providers"]: mu_f=mu_f+(X[:,5:]@P["provider_len"])[...,None]
        zf=(lrt-mu_f)/sd_f;zs=(lrt-mu_s)/sd_s
        len_f=np.where(c3,norm.logsf(zf),norm.logpdf(zf)-np.log(sd_f)-lrt)
        len_s=np.where(c3,norm.logsf(zs),norm.logpdf(zs)-np.log(sd_s)-lrt)
        eta_f=P["beta_f"][ci][...,None]+cc*P["gacc_f"][None,:,None]+effect("b_f","tau_bf")
        eta_s=P["beta_s"][None,:,None]+P["beta_s_len"][None,:,None]*(lrt-np.log(160))
        sign=np.where(y==1,1.,-1.)[:,None,None]
        cor_f=np.where(c3,0.,-np.logaddexp(0,-sign*eta_f));cor_s=np.where(c3,0.,-np.logaddexp(0,-sign*eta_s))
        log_p=-np.logaddexp(0,-logit_slow);log_1mp=-np.logaddexp(0,logit_slow)
        length=np.logaddexp(log_1mp+len_f,log_p+len_s)
        joint=np.logaddexp(log_1mp+len_f+cor_f,log_p+len_s+cor_s)
    else:
        v=(X@P["v_coefs"])[...,None]+effect("u_v","tau_v")
        a=np.broadcast_to(np.exp(X@P["a_coefs"])[...,None],v.shape)
        log_t=(X@P["t_coefs"])[...,None]
        if "tq" in name: log_t=log_t+effect("u_t","tau_t")
        t=np.broadcast_to(np.exp(log_t),v.shape)
        sv=np.zeros_like(v)
        if "sdv" in name: sv=np.broadcast_to(np.exp(P["sv_coefs"][0][None,:,None]+code[:,None,None]*P["sv_coefs"][1][None,:,None]),v.shape)
        rr=np.broadcast_to(rt[:,None,None],v.shape);response=np.broadcast_to(np.where(y==1,1,-1)[:,None,None],v.shape)
        joint=evaluate(rr,response,v,a,t,sv);other=evaluate(rr,-response,v,a,t,sv)
        length=np.logaddexp(joint,other)
        if cens.any():
            survival=evaluate(rr[cens],0,v[cens],a[cens],t[cens],sv[cens],censored=True)
            joint[cens]=survival;length[cens]=survival
        if "lapse" in name:
            e=P["epsilon"][None,:,None]
            c_len=np.where(cens,norm.logsf((np.log(rt)-np.log(20))/2),norm.logpdf(np.log(rt),np.log(20),2)-np.log(rt))[:,None,None]
            c_joint=c_len-np.where(cens,0,np.log(2))[:,None,None]
            joint=np.logaddexp(np.log1p(-e)+joint,np.log(e)+c_joint)
            length=np.logaddexp(np.log1p(-e)+length,np.log(e)+c_len)
    joint=sp.logsumexp(joint.reshape(n,-1),axis=1)-np.log(S*M)
    length=sp.logsumexp(length.reshape(n,-1),axis=1)-np.log(S*M)
    return dict(joint=joint,length=length,correctness_given_length=joint-length)


def cv(d, scenario, models, args, k=5, secondary=False, provider_adjust=False):
    ids=np.array(sorted(d.qid.unique()));np.random.default_rng(SEED).shuffle(ids)
    folds=np.array_split(ids,k);pieces=[]
    if secondary:
        splits=[(-1,d[d.rep%2==0],d[d.rep%2==1])]
    else: splits=[(i,d[~d.qid.isin(qs)],d[d.qid.isin(qs)]) for i,qs in enumerate(folds)]
    for i,train,test in splits:
        label=f"{scenario}_{'within' if secondary else f'fold{i}'}"
        test=test.copy()
        for name in models:
            scorepath=OUT/f"{label}_{name}_scores.csv"
            if scorepath.exists(): score=pd.read_csv(scorepath)
            else:
                print(f"Starting {label} {name}: {len(train)} train / {len(test)} test",flush=True)
                P=fit_model(train,name,f"{label}_{name}",args,provider_adjust)
                predictions=predict(P,test,own=secondary,seed=SEED+i+1,
                                    analytic=getattr(args,"analytic_prediction",False))
                score=test[[c for c in ["qid","condition","rep","provider","has_code","rt","correct","censored"] if c in test]].copy()
                for comp,vals in predictions.items(): score[f"lpd_{name}_{comp}"]=vals
                score["fold"]=i;score.to_csv(scorepath,index=False)
            for comp in COMPONENTS: test[f"lpd_{name}_{comp}"]=score[f"lpd_{name}_{comp}"].to_numpy()
        test["fold"]=i;pieces.append(test)
        pd.concat(pieces).to_csv(OUT/f"{scenario}_{'within' if secondary else 'cv'}_per_trial.csv",index=False)
    frame=pd.concat(pieces)
    tables=[comparison(frame,name,target="within-question repeats" if secondary else "held-out questions") for name in models if name!="baseline"]
    if tables: pd.concat(tables).to_csv(OUT/f"{scenario}_{'within' if secondary else 'cv'}_comparison.csv",index=False)
    return frame


def accuracy_fit(d, label, args, provider_adjust=False):
    d=d[(d.outcome=="answered")&(d.reasoning_tokens>0)].copy()
    qidx,qids=pd.factorize(d.qid);x=np.log2(d.reasoning_tokens)
    means=x.groupby(d.qid).transform("mean");within=(x-means).to_numpy();between=(means-means.mean()).to_numpy()
    providers=sorted(d.provider.unique())[1:] if provider_adjust else []
    X,names=matrix(d,providers);X=X[:,1:]
    # Dataset controls the targeted selection/provider change in the combined fit.
    phase=(d.phase=="cap_experiment").astype(float).to_numpy()
    position=d.correct_is_A.astype(float).to_numpy()-.5
    with pm.Model() as model:
        intercept=pm.Normal("intercept",2,2)
        slope=pm.Normal("within_question_log2_length",0,1.5)
        b_slope=pm.Normal("between_question_log2_length",0,1.5)
        terms=pm.Normal("condition_and_code",0,1.5,shape=X.shape[1])
        phase_b=pm.Normal("cap_phase",0,1.5);position_b=pm.Normal("correct_option_A",0,1.5)
        tau=pm.HalfNormal("tau_question",1.5);u=pm.Normal("u",0,1,shape=len(qids))*tau
        eta=intercept+slope*within+b_slope*between+X@terms+phase_b*phase+position_b*position+u[qidx]
        pm.Bernoulli("correct",logit_p=eta,observed=d.correct.astype(int))
    idata=sample_model(model,label,args)
    draws=idata.posterior["within_question_log2_length"].values.flatten()
    return dict(dataset=label,n=len(d),questions=len(qids),errors=int((d.correct==False).sum()),
                log_odds_per_doubling=float(draws.mean()),lo=float(np.quantile(draws,.025)),hi=float(np.quantile(draws,.975)),
                odds_ratio=float(np.exp(draws.mean())),or_lo=float(np.exp(np.quantile(draws,.025))),or_hi=float(np.exp(np.quantile(draws,.975))),
                probability_negative=float((draws<0).mean()))


def fits(args):
    main=data()
    models=["baseline"]+(args.models or ["ddm_lapse","ddm_sdv_lapse"])
    if "main" in args.scenarios:
        cv(main,"main",models,args)
        cv(main,"main",models,args,secondary=True)
    for scenario in [x for x in args.scenarios if x!="main"]:
        cv(data(scenario),scenario,models,args,k=3,provider_adjust=scenario=="provider_adjusted")
    accuracy(args)


def accuracy(args):
    r1=pd.read_csv(OUT/"pilot_r1_with_provider.csv")
    r1=r1[(r1.outcome!="answered")|(r1.reasoning_tokens<=8192)]
    cap=pd.read_csv(OUT/"cap_experiment_with_provider.csv")
    slopes=[accuracy_fit(d,f"accuracy_{label}",args) for label,d in [("step1",r1),("cap",cap),("combined",pd.concat([r1,cap]))]]
    slopes.append(accuracy_fit(pd.concat([r1,cap]),"accuracy_combined_provider",args,provider_adjust=True))
    pd.DataFrame(slopes).to_csv(OUT/"accuracy_length.csv",index=False)


def baselines(args):
    cv(data(),"main",["baseline"],args)
    cv(data(),"main",["baseline"],args,secondary=True)
    for scenario in ["exclude_incomplete","hidden_only","deepinfra","provider_adjusted"]:
        cv(data(scenario),scenario,["baseline"],args,k=3,provider_adjust=scenario=="provider_adjusted")


def recovery_data(n_questions, seed, generator="drift", question_t=True):
    import hssm
    rng=np.random.default_rng(seed);rows=[]
    for q in range(n_questions):
        code=int(rng.random()<.44);uq=rng.normal(0,.15);ut=rng.normal(0,.35) if question_t else 0.
        for ci,condition in enumerate(CONDITIONS):
            s=int(condition.startswith("sbs"));i=int(condition.endswith("thorough"))
            v=.45-.25*code+uq+(.15*s if generator=="drift" else 0)
            a=3.5*np.exp(.7*code+.15*i+(np.log(1.33)*s if generator=="boundary" else 0))
            t=.5*np.exp(1.0*code+.2*i+ut)
            sv=.25*np.exp(.3*code) if generator!="fixed" else 0.
            for rep in range(2):
                actual_v=rng.normal(v,sv)
                sim=hssm.simulate_data("ddm",dict(v=actual_v,a=a,z=.5,t=t),size=1,random_state=int(rng.integers(2**31-1)),max_t=2000.,delta_t=.005)
                rt=float(sim.rt.iloc[0]);correct=bool(sim.response.iloc[0]>0)
                if generator=="lognormal":
                    rt=float(np.exp(np.log(20)+code+uq+rng.normal(0,.6)));correct=bool(rng.random()<sp.expit(2-code-.4*np.log(rt/20)))
                cens=rt>327.68
                rows.append(dict(qid=f"q{q:04d}",condition=condition,scaffold="step_by_step" if s else "plain",instruction="thorough" if i else "concise",rep=rep,
                                 correct_is_A=correct_is_a(f"q{q:04d}",condition,rep,CONDITIONS,seed),has_code=code,ci=ci,correct=float(correct),response=1 if correct else -1,
                                 rt=min(rt,327.68),dl=327.68 if cens else np.nan,censored=cens,provider="simulation",outcome="censored" if cens else "answered"))
    return pd.DataFrame(rows)


def recovery(args):
    checks=[]
    # Replicate parameter recovery at the proposed 400-question x 2-repeat size.
    for seed in [SEED+101,SEED+102]:
        for generator in ["drift","boundary"]:
            label=f"recovery400_{generator}_{seed}"
            path=OUT/f"{label}.csv"
            if path.exists():d=pd.read_csv(path)
            else:d=recovery_data(400,seed,generator);d.to_csv(path,index=False)
            P=fit_model(d,"ddm_sdv_tq_lapse",label,args)
            info=json.loads((OUT/"posteriors"/f"{label}_diagnostics.json").read_text())
            flagged=bool(info["divergences"] or info["max_rhat"]>1.05 or info["min_ess"]<50)
            for parameter,truth in [("v_coefs",.15 if generator=="drift" else 0.),("a_coefs",np.log(1.33) if generator=="boundary" else 0.)]:
                x=P[parameter][1];lo,hi=np.quantile(x,[.025,.975])
                checks.append(dict(seed=seed,generator=generator,parameter=parameter+"_scaffold",truth=truth,mean=float(x.mean()),lo=float(lo),hi=float(hi),covered=bool(lo<=truth<=hi),excludes_zero=bool(lo>0 or hi<0),diagnostic_flag=flagged))
            for code in [0,1]:
                x=np.exp(P["sv_coefs"][0]+code*P["sv_coefs"][1]);truth=.25*np.exp(.3*code);lo,hi=np.quantile(x,[.025,.975])
                checks.append(dict(seed=seed,generator=generator,parameter=f"sv_code{code}",truth=truth,mean=float(x.mean()),lo=float(lo),hi=float(hi),covered=bool(lo<=truth<=hi),excludes_zero=True,diagnostic_flag=flagged))
            pd.DataFrame(checks).to_csv(OUT/"recovery_two_repeat_parameters.csv",index=False)
    # Predictive recovery also needs a non-accumulation control. Small replicated
    # 50-question datasets permit grouped CV without treating repeats as units.
    for seed in [SEED+201,SEED+202]:
        for generator in ["drift","fixed","lognormal"]:
            label=f"recovery50_{generator}_{seed}";path=OUT/f"{label}.csv"
            if path.exists():d=pd.read_csv(path)
            else:d=recovery_data(50,seed,generator);d.to_csv(path,index=False)
            cv(d,label,["baseline","ddm_sdv_lapse"],args,k=3)
    predictive400(args)


def predictive400(args):
    # Exact candidate/baseline generators at the full proposed question count.
    # Keep non-decision time fixed by condition for the ddm_sdv candidate tested
    # here; the separate parameter-recovery checks include question-level t.
    for generator in ["drift","lognormal"]:
        seed=SEED+301;label=f"predictive400_{generator}_{seed}";path=OUT/f"{label}.csv"
        if path.exists():d=pd.read_csv(path)
        else:d=recovery_data(400,seed,generator,question_t=False);d.to_csv(path,index=False)
        cv(d,label,["baseline","ddm_sdv_lapse"],args,k=3)


def summarize():
    infos=[json.loads(p.read_text()) for p in (OUT/"posteriors").glob("*_diagnostics.json")]
    if infos:pd.DataFrame(infos).to_csv(OUT/"all_diagnostics.csv",index=False)
    info_by_label={x["label"]:x for x in infos}
    # Rebuild comparisons from model-specific checkpoints. Separate workers can
    # fit different models; partial fold coverage must never become a verdict.
    groups={}
    names=["ddm_sdv_lapse","ddm_tq_lapse","ddm_lapse","two_process","baseline"]
    for path in OUT.glob("*_scores.csv"):
        stem=path.stem.removesuffix("_scores")
        name=next((n for n in names if stem.endswith("_"+n)),None)
        if name is None:continue
        label=stem[:-(len(name)+1)]
        match=re.fullmatch(r"(.+)_(fold\d+|within)",label)
        if match is None:continue
        scenario,split=match.groups();target="within" if split=="within" else "cv"
        groups.setdefault((scenario,target),{}).setdefault(name,[]).append((label,pd.read_csv(path)))
    frames=[];statuses=[];direct=[]
    keys=["qid","condition","rep"]
    for (scenario,target),models in groups.items():
        if "baseline" not in models:continue
        baseline=pd.concat([x[1] for x in models["baseline"]],ignore_index=True)
        expected=5 if scenario=="main" else 3
        expected=1 if target=="within" else expected
        if len(models["baseline"])!=expected:continue
        basekeys=set(map(tuple,baseline[keys].to_numpy()))
        combined=baseline.copy();group_tables=[]
        for name,parts in models.items():
            if name=="baseline":continue
            candidate=pd.concat([x[1] for x in parts],ignore_index=True)
            complete=set(map(tuple,candidate[keys].to_numpy()))==basekeys and len(parts)==expected
            statuses.append(dict(analysis=f"{scenario}_{target}",model=name,complete=complete,folds=len(parts),expected_folds=expected))
            if not complete:continue
            combined=combined.merge(candidate[keys+[f"lpd_{name}_{c}" for c in COMPONENTS]],on=keys,validate="one_to_one")
            merged=baseline.merge(candidate[keys+[f"lpd_{name}_{c}" for c in COMPONENTS]],on=keys,validate="one_to_one")
            tab=comparison(merged,name,target="within-question repeats" if target=="within" else "held-out questions")
            diag=[info_by_label[label+"_"+model] for model in ["baseline",name] for label,_ in models[model]]
            tab["analysis"]=f"{scenario}_{target}";tab["max_rhat"]=max(x["max_rhat"] for x in diag)
            tab["min_ess"]=min(x["min_ess"] for x in diag);tab["divergences"]=sum(x["divergences"] for x in diag)
            tab["diagnostic_flag"]=(tab.max_rhat>1.05)|(tab.min_ess<50)|(tab.divergences>0)
            tab["score_verdict"]=tab.verdict
            tab.loc[tab.diagnostic_flag,"verdict"]="unreliable fit; no verdict"
            frames.append(tab)
            group_tables.append(tab)
            merged.to_csv(OUT/f"{scenario}_{target}_{name}_paired_scores.csv",index=False)
        combined.to_csv(OUT/f"{scenario}_{target}_per_trial.csv",index=False)
        if group_tables:pd.concat(group_tables).to_csv(OUT/f"{scenario}_{target}_comparison.csv",index=False)
        if all(n in models and len(models[n])==expected for n in ["ddm_lapse","ddm_sdv_lapse"]):
            left=pd.concat([x[1] for x in models["ddm_lapse"]],ignore_index=True)
            right=pd.concat([x[1] for x in models["ddm_sdv_lapse"]],ignore_index=True)
            merged=left.merge(right[keys+[f"lpd_ddm_sdv_lapse_{c}" for c in COMPONENTS]],on=keys,validate="one_to_one")
            if len(merged)==len(baseline):
                tab=comparison(merged,"ddm_sdv_lapse","ddm_lapse",target="within-question repeats" if target=="within" else "held-out questions")
                diag=[info_by_label[label+"_"+model] for model in ["ddm_lapse","ddm_sdv_lapse"] for label,_ in models[model]]
                tab["analysis"]=f"{scenario}_{target}"
                tab["diagnostic_flag"]=any(x["divergences"] or x["max_rhat"]>1.05 or x["min_ess"]<50 for x in diag)
                tab["verdict"]=tab.verdict.replace({"baseline better":"fixed drift better","candidate better":"variable drift better"})
                tab.loc[tab.diagnostic_flag,"verdict"]="unreliable fit; no verdict"
                direct.append(tab)
    if frames:pd.concat(frames).to_csv(OUT/"all_comparisons.csv",index=False)
    if statuses:pd.DataFrame(statuses).to_csv(OUT/"completion_status.csv",index=False)
    if direct:pd.concat(direct).to_csv(OUT/"variable_vs_fixed_comparisons.csv",index=False)
    print("Saved combined comparisons and diagnostics.",flush=True)


if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--stage",choices=["prepare","baselines","accuracy","fits","recovery","predictive400","summarize","all"],default="all")
    ap.add_argument("--draws",type=int,default=400);ap.add_argument("--tune",type=int,default=500)
    ap.add_argument("--models",nargs="+",choices=["ddm_lapse","ddm_tq_lapse","ddm_sdv_lapse","two_process"])
    ap.add_argument("--scenarios",nargs="+",choices=["main","exclude_incomplete","hidden_only","deepinfra","provider_adjusted"],default=["main","exclude_incomplete","hidden_only","deepinfra","provider_adjusted"])
    args=ap.parse_args()
    if args.stage=="baselines": baselines(args)
    if args.stage=="accuracy": accuracy(args)
    if args.stage=="predictive400": predictive400(args)
    for name,fn in [("prepare",prepare),("fits",lambda:fits(args)),("recovery",lambda:recovery(args)),("summarize",summarize)]:
        if args.stage in [name,"all"]:fn()
