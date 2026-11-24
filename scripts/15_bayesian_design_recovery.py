"""Full hierarchical Bayesian confirmation of two preselected recovery cases.

Same likelihood and priors as 08; centered effects and a dense mass matrix,
initialized from the public pilot fits, to handle realistic large q variation.
New-question prediction integrates Normal effects analytically. No API calls.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ddm-mpl')
os.environ.setdefault('PYTENSOR_FLAGS','base_compiledir=/tmp/ddm-pytensor,mode=FAST_RUN')
import argparse,importlib.util,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
import recovery_marginal as m

ROOT=Path(__file__).resolve().parents[1]
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=['ddm_calibrated','baseline_calibrated'],required=True)
    ap.add_argument('--fold',type=int);a=ap.parse_args();s=load('suite','12_design_recovery.py');r=load('robustness','08_robustness.py')
    lib,_,_=s.library();init={}
    for name in s.MODELS:
        theta=np.median(np.concatenate([x for x,_ in lib[name]]),axis=0);P={k:np.asarray(v) for k,v in m.unpack(theta,name).items()}
        if name=='baseline':init[name]=P
        else:init[name]=dict(v_coefs=P['v'],a_coefs=P['a'],t_coefs=P['t'],tau_v=P['tau_v'],sv_coefs=P['sv'],epsilon=P['epsilon'])
    r.OUT=s.OUT/'bayesian_dense';r.OUT.mkdir(exist_ok=True);(r.OUT/'posteriors').mkdir(exist_ok=True);r.SEED=s.SEED
    settings=SimpleNamespace(draws=600,tune=1200,chains=4,target_accept=.95,dense_mass=True,centered_effects=True,
                             analytic_prediction=True,initial_hyperparameters=init)
    s.dump(r.OUT/'settings.json',dict(draws=600,tune=1200,chains=4,target_accept=.95,dense_mass=True,
                                    centered_effects=True,population_initialization='Median of joint public R1 posterior draws, independent of simulated truth.',
                                    prediction='Analytic population Normal convolution, 64-node logistic-Normal quadrature, 128-node survival.',
                                    diagnostics='No divergences; max Rhat <=1.05; min bulk ESS >=50.'))
    d=s.censor(pd.read_csv(s.OUT/'data'/f'{a.profile}_00.csv'),32768)
    if a.fold is None:r.cv(d,f'{a.profile}_00_cap32768',s.MODELS,settings,k=3)
    else:
        ids=np.array(sorted(d.qid.unique()));np.random.default_rng(s.SEED).shuffle(ids)
        held=np.array_split(ids,3)[a.fold];train=d[~d.qid.isin(held)];test=d[d.qid.isin(held)].copy()
        for name in s.MODELS:
            label=f'{a.profile}_00_cap32768_fold{a.fold}_{name}'
            P=r.fit_model(train,name,label,settings);pred=r.predict(P,test,analytic=True)
            for component,val in pred.items():test[f'lpd_{name}_{component}']=val
            columns=['qid','condition','rep','has_code','rt','correct','censored']+[x for x in test if x.startswith(f'lpd_{name}_')]
            test[columns].to_csv(r.OUT/f'{label}_scores.csv',index=False)


if __name__=='__main__':main()
