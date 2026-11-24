"""Numerical and design checks required before interpreting new fits."""
import os
os.environ.setdefault("MPLCONFIGDIR","/tmp/ddm-mpl")
os.environ.setdefault("PYTENSOR_FLAGS","base_compiledir=/tmp/ddm-pytensor,mode=FAST_RUN")
import json
import importlib.util
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytensor
import pytensor.tensor as pt
from scipy.integrate import quad
from diffusion_likelihood import evaluate, log_density, log_survival
from design import correct_is_a


def main():
    checks=[]
    for v,a,t,sv in [(.5,2,.3,0),(.5,2,.3,.2),(.5,2,.3,1),(4,15,.5,0),(.1,10,2,.5)]:
        density=lambda rt:sum(float(np.exp(evaluate(rt,r,v,a,t,sv))) for r in [-1,1])
        mass=quad(density,t,np.inf,epsabs=1e-9,limit=300)[0]
        assert abs(mass-1)<1e-6,(v,a,t,sv,mass)
        C=t+(a*a)/(1+abs(v*a)/(1+sv*a))
        numerical=quad(density,C,np.inf,epsabs=1e-10,limit=300)[0]
        p64=float(np.exp(evaluate(C,0,v,a,t,sv,censored=True,nodes=64)))
        p128=float(np.exp(evaluate(C,0,v,a,t,sv,censored=True,nodes=128)))
        assert abs(p64-numerical)<1e-6,(p64,numerical)
        assert abs(p64-p128)<1e-6
        checks.append(dict(v=v,a=a,t=t,sv=sv,mass=mass,survival_quad=numerical,survival64=p64,survival128=p128))
    from hssm.likelihoods.analytical import logp_ddm_sdv
    xs=[pt.dvector(n) for n in ["rt","r","v","a","z","t","sv"]]
    f=pytensor.function(xs,logp_ddm_sdv(pt.stack(xs[:2],axis=1),*xs[2:]),on_unused_input="ignore")
    rt=np.array([.6,1,3,10,81.92]);v=np.full(5,.5);a=np.full(5,2);t=np.full(5,.3)
    for sv in [.2,1.]:
        ours=evaluate(rt,1,v,a,t,sv);reference=f(rt,np.ones(5),v,a,np.full(5,.5),t,np.full(5,sv))
        assert np.max(abs(ours-reference))<1e-10
    # NumPy scoring and differentiable training evaluate the same law.
    ys=[pt.dvector(n) for n in ["rt","r","v","a","t","sv"]]
    density_graph=pytensor.function(ys,log_density(*ys))
    surv_graph=pytensor.function(ys,log_survival(ys[0],*ys[2:]),on_unused_input="ignore")
    arrays=[rt,np.ones(5),v,a,t,np.full(5,.2)]
    assert np.max(abs(density_graph(*arrays)-evaluate(*arrays)))<1e-10
    assert np.max(abs(surv_graph(*arrays)-evaluate(*arrays,censored=True)))<1e-10
    assert evaluate(.1,1,.5,2,.3)==-np.inf
    assert evaluate(.1,1,.5,2,.3,censored=True)==0.
    conditions=["plain_concise","plain_thorough","sbs_concise","sbs_thorough"]
    for q in range(100):
        assignments=[[correct_is_a(str(q),c,r,conditions,20261006) for c in conditions] for r in range(2)]
        assert all(sum(row)==2 for row in assignments)
        assert all(sum(assignments[r][c] for r in range(2))==1 for c in range(4))
    # Historical high-cap logs must not inherit the current 8,192 config cap.
    spec=importlib.util.spec_from_file_location("baseline_cv",Path(__file__).with_name("07_baseline_cv.py"))
    cv=importlib.util.module_from_spec(spec);spec.loader.exec_module(cv)
    r1=cv.load("results/pilot_r1.csv");cap=cv.load("results/cap_experiment.csv")
    assert len(r1)==400 and r1.censored.sum()==171
    assert len(cap)==62 and cap.censored.sum()==12
    assert np.allclose(cap.loc[cap.censored,"dl"],245.76)
    mixed=pd.read_csv("results/pilot_r1.csv").iloc[:4].copy()
    mixed["token_cap"]=[8192,24576,8192,24576];mixed["outcome"]="answered";mixed["rt"]=100.;mixed["correct"]=True
    with tempfile.NamedTemporaryFile(suffix=".csv") as f:
        mixed.to_csv(f.name,index=False)
        assert cv.load(f.name).censored.tolist()==[True,False,True,False]
    assert np.isclose(cv.clustered_se(np.array([1.,2.,3.,4.]),np.array(["a","a","b","b"])),4.)
    # Regression for remote-tail JAX gradients that invalidated the initial
    # baseline fits. The asymptotic branch's error is below 1e-6 log units.
    spec=importlib.util.spec_from_file_location("robustness",Path(__file__).with_name("08_robustness.py"))
    robust=importlib.util.module_from_spec(spec);spec.loader.exec_module(robust)
    from scipy.stats import norm
    z=pt.dvector("z");sf=robust.normal_logsf(z)
    check_sf=pytensor.function([z],[sf,pt.grad(sf.sum(),z)],mode="JAX")
    values=np.array([-100.,-8.,0.,8.,8.01,50.,100.])
    logsf,gradient=check_sf(values)
    assert np.isfinite(gradient).all()
    assert np.max(np.abs(logsf-norm.logsf(values)))<1e-6
    pd.DataFrame(checks).to_csv("results/robustness/likelihood_validation.csv",index=False)
    print("PASS: normalisation, survival quadrature/node doubling, HSSM density agreement, training/scoring parity, support, option counterbalancing, collection caps, clustered SE, and remote-tail JAX gradients.")


if __name__=="__main__":main()
