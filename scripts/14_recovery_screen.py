"""Replicated composite-likelihood SCREENING, not full Bayesian power.

Uses exactly the generated datasets in 12, grouped three-fold validation and
the same marginal predictive model families. Trial dependence is generated and
used for uncertainty; fitting uses composite likelihood (no covariance term).
Results must be checked against hierarchical and Bayesian selected-case fits.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ddm-mpl')
import argparse,importlib.util,json,time
import numpy as np
import pandas as pd
import recovery_marginal as m
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location('suite',ROOT/'scripts/12_design_recovery.py')
s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
BASE=s.OUT


def case_fit(d,case,initials):
    out=s.OUT;path=out/'scores'/f'{case}.csv';diagpath=out/'fits'/f'{case}.json'
    if path.exists() and diagpath.exists():return
    ids=np.array(sorted(d.qid.unique()));np.random.default_rng(s.SEED).shuffle(ids)
    diags=[];pieces=[]
    for fold,held in enumerate(np.array_split(ids,3)):
        train=ids[~np.isin(ids,held)];data,ordered=m.prepare(d,train)
        test=ordered[ordered.qid.isin(held)].copy();mask=ordered.qid.isin(held).to_numpy()
        for name in s.MODELS:
            cache=out/'fits'/f'{case}_fold{fold}_{name}.json'
            if cache.exists():record=json.loads(cache.read_text());theta=np.asarray(record['theta'])
            else:
                start=time.time();runs=[]
                for i in range(2):
                    theta=initials[name].copy()
                    if i:theta+=np.random.default_rng(s.SEED+fold).normal(0,.12,len(theta))
                    result,_=m.fit(d,train,name,theta,method='composite',maxiter=500);runs.append(result)
                best=min(runs,key=lambda r:r.fun if np.isfinite(r.fun) else np.inf);theta=best.x
                spread=max(r.fun for r in runs)-best.fun
                record=dict(fit_version=5,method='composite',model=name,fold=fold,theta=theta.tolist(),
                            objective=float(best.fun),gradient_max=float(np.abs(best.jac).max()),
                            convergence=bool(best.success),start_objective_spread=float(spread),iterations=int(best.nit),seconds=time.time()-start,
                            valid=bool(best.success and np.abs(best.jac).max()<.5 and spread<2))
                s.dump(cache,record)
            predictions=m.point_predict(theta,name,data)
            for component,values in predictions.items():test[f'lpd_{name}_{component}']=values[mask]
            diags.append(record)
        test['fold']=fold;pieces.append(test)
    path.parent.mkdir(parents=True,exist_ok=True);pd.concat(pieces).to_csv(path,index=False);s.dump(diagpath,diags)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=s.PROFILES+s.EXTENSIONS);ap.add_argument('--stage',choices=['fit','summarize'],default='fit');a=ap.parse_args()
    plan=json.loads((BASE/'plan.json').read_text());lib,_,_=s.library()
    initials={name:np.median(np.concatenate([x for x,_ in lib[name]]),axis=0) for name in s.MODELS}
    s.OUT=BASE/'composite';s.OUT.mkdir(exist_ok=True)
    frozen=dict(design_plan='../plan.json',replicates=plan['replicates'],questions=plan['questions'],folds=3,
                method='Composite likelihood MAP of trial marginals, with priors from 08. This is approximate screening; within-question covariance is omitted from fitting, retained in generation and question-level uncertainty.',
                validation='Hierarchical MAP for first replicate of all six scenarios; full Bayesian comparison for first replicate of both calibrated scenarios, chosen in the design plan.',
                diagnostics='Two starts; optimizer convergence, max gradient <0.5, objective spread <2 nats. Failures stay in rate denominators.')
    target=s.OUT/'plan.json'
    if target.exists():assert json.loads(target.read_text())==frozen
    else:s.dump(target,frozen)
    s.PROFILES=s.PROFILES+s.EXTENSIONS
    if a.stage=='summarize':s.summarize(plan);return
    for profile in ([a.profile] if a.profile else s.PROFILES):
        for rep in range(plan['replicates']):
            d=pd.read_csv(BASE/'data'/f'{profile}_{rep:02d}.csv')
            for cap in plan['caps_tokens']:
                case=f'{profile}_{rep:02d}_cap{cap}';print(f'Composite screen {case}',flush=True)
                case_fit(s.censor(d,cap),case,initials)
    s.summarize(plan)


if __name__=='__main__':main()
