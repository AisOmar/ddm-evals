"""Independent numerical and design checks for replicated recovery screening."""
import sys,json,pathlib,importlib.util
import numpy as np
import pandas as pd
from scipy.integrate import quad
from scipy.special import logsumexp,expit
from scipy.stats import norm
from scipy.optimize import minimize_scalar
from scipy.optimize._numdiff import approx_derivative
from ssms.basic_simulators.simulator import simulator
import recovery_marginal as m
from diffusion_likelihood import evaluate
import diffusion_likelihood as dl
from functools import lru_cache
dl.leggauss=lru_cache(maxsize=8)(dl.leggauss)

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('suite',ROOT/'scripts/12_design_recovery.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


def question_reference(theta,name,d):
    """Direct scalar adaptive integration, independent of Gaussian proposals."""
    P={k:np.asarray(v) for k,v in m.unpack(theta,name).items()}
    rt=np.asarray(d['rt'])[0];c=np.asarray(d['cens'])[0];y=np.asarray(d['y'])[0]
    code=np.asarray(d['code'])[0];ci=np.asarray(d['ci'])[0];X=np.asarray(d['X'])[0]
    def integrate(fun):
        # Locate the scale on a grid; integrate the complete prior range in pieces.
        grid=np.linspace(-10,10,161);h=max(fun(z) for z in grid)
        values=[quad(lambda z:np.exp(fun(z)-h),left,right,epsabs=1e-10,epsrel=1e-8,limit=100)[0]
                for left,right in zip(grid[:-1],grid[1:])]
        return h+np.log(sum(values))
    if name=='baseline':
        mu=P['alpha'][ci]+P['gamma_len']*code;sd=P['sigma'][ci];lrt=np.log(rt)
        def length(z):
            u=z*P['tau_u'];lp=np.where(c,norm.logsf((lrt-mu-u)/sd),norm.logpdf(lrt,mu+u,sd)-lrt)
            return lp.sum()+norm.logpdf(z)
        eta=P['beta'][ci]+P['gamma_acc']*code+P['beta_len']*(lrt-float(d['centre']))
        def acc(z):
            x=eta+z*P['tau_b'];return np.where(c,0,y*x-np.logaddexp(0,x)).sum()+norm.logpdf(z)
        return integrate(length)+integrate(acc)
    v=X@P['v'];a=np.exp(X@P['a']);t=np.exp(X@P['t']);sv=np.exp(P['sv'][0]+code*P['sv'][1]);e=P['epsilon']
    cl=np.where(c,norm.logsf((np.log(rt)-np.log(20))/2),norm.logpdf(np.log(rt),np.log(20),2)-np.log(rt)-np.log(2))
    def joint(z):
        vv=v+z*P['tau_v'];lp=evaluate(rt,2*y-1,vv,a,t,sv)
        lp[c]=evaluate(rt[c],0,vv[c],a[c],t[c],sv[c],censored=True,nodes=128)
        return np.logaddexp(np.log1p(-e)+lp,np.log(e)+cl).sum()+norm.logpdf(z)
    return integrate(joint)


def main():
    out=s.OUT;plan=json.loads((out/'plan.json').read_text());checks={}
    # Simulator convention and finite time-step accuracy, using an empirical CDF.
    n=20000;sim=simulator(np.array([.5,3,.5,.5],np.float32),model='ddm',n_samples=n,delta_t=.005,
                          max_t=327.68,smooth_unif=False,random_state=20261010)
    rt=sim['rts'].ravel();acc=float((sim['choices'].ravel()>0).mean())
    C=np.array([2.,5.,10.,20.]);emp=np.array([(rt>x).mean() for x in C])
    true=np.exp(evaluate(C,0,.5,3.,.5,0.,censored=True,nodes=128))
    checks['simulator_accuracy']=dict(empirical=acc,exact=float(expit(3)),n=n)
    checks['simulator_cdf']=dict(deadlines=C.tolist(),empirical_survival=emp.tolist(),exact_survival=true.tolist(),max_error=float(np.max(np.abs(emp-true))))
    assert abs(acc-expit(3))<.015 and np.max(np.abs(emp-true))<.015
    # Shared-tail mesh compared with each drift's independent rational mesh.
    a=np.array([3.,20.,50.]);t=np.full(3,.2);sv=np.array([.2,.1,.2]);mean=np.full(3,.8)
    v=np.tile(np.array([-.5,0,.5,1.5]),(3,1));C=np.array([2.,81.92,327.68])
    shared=np.asarray(m.survival_shared(C,v,a,t,sv,mean,64))
    exact=evaluate(C[:,None],0,v,a[:,None],t[:,None],sv[:,None],censored=True,nodes=256)
    checks['tail_mesh_max_log_error']=float(np.max(np.abs(shared-exact)))
    assert checks['tail_mesh_max_log_error']<.002
    # All conditions have balanced answer positions in each two-repeat cell.
    for path in (out/'data').glob('*.csv'):
        d=pd.read_csv(path);assert len(d)==plan['questions']*8
        assert d.groupby(['qid','ci']).correct_is_A.sum().eq(1).all()
        assert d.groupby(['qid','rep']).correct_is_A.sum().eq(2).all()
    checks['option_balance']='all generated datasets checked'
    # Check exact integration against our approximate marginal for diverse qids.
    lib,_,_=s.library();errors=[];grad=[]
    for name,profile in [('baseline','baseline_calibrated'),('ddm_sdv_lapse','ddm_calibrated')]:
        d=s.censor(pd.read_csv(out/'data'/f'{profile}_00.csv'),32768)
        meta=json.loads((out/'data'/f'{profile}_00.json').read_text());theta=np.asarray(meta['theta'])
        # Choose short, medium, heavily censored and inaccurate questions.
        stats=d.groupby('qid').agg(rt=('rt','median'),c=('censored','sum'),accuracy=('correct','mean'))
        ids=list(dict.fromkeys([stats.rt.idxmin(),stats.rt.sort_values().index[len(stats)//2],stats.c.idxmax(),stats.accuracy.idxmin()]))
        for qid in ids:
            one=d[d.qid==qid];data,_=m.prepare(one,[qid]);ref=question_reference(theta,name,data)
            approx={str(n):float(m.question_logp(theta,name,data,n,128)[0]) for n in [16,32,64]}
            errors.append(dict(model=name,qid=qid,reference=ref,approximate=approx,error16=approx['16']-ref,error64=approx['64']-ref))
        one=d[d.qid==ids[1]];data,_=m.prepare(one,[ids[1]]);fun=m.objective(name,32,64)
        analytic=np.asarray(fun(theta,data)[1]);numeric=approx_derivative(lambda x:float(fun(x,data)[0]),theta,method='3-point').ravel()
        error=float(np.max(np.abs(analytic-numeric)));grad.append(dict(model=name,max_abs_error=error));assert error<.002
    checks['direct_question_integration']=errors;checks['gradient_checks']=grad
    parity=[]
    for name,profile in [('baseline','baseline_calibrated'),('ddm_sdv_lapse','ddm_calibrated')]:
        frame=s.censor(pd.read_csv(out/'data'/f'{profile}_00.csv'),32768)
        theta=np.asarray(json.loads((out/'data'/f'{profile}_00.json').read_text())['theta'])
        data,_=m.prepare(frame,frame.qid.unique())
        jax_value=np.asarray(m.composite_question_logp(theta,name,data))
        numpy_value=m.point_predict(theta,name,data)['joint'].reshape(-1,8).sum(axis=1)
        error=float(np.max(np.abs(jax_value-numpy_value)))
        parity.append(dict(model=name,max_abs_error=error));assert error<1e-5
    checks['composite_training_prediction_parity']=parity
    # This gate tests quadrature itself, not whether a model wins.
    checks['question_quadrature_64_pass']=all(abs(x['error64'])<.02 for x in errors)
    checks['question_quadrature_16_max_error']=max(abs(x['error16']) for x in errors)
    s.dump(out/'numerical_validation.json',checks)
    print(json.dumps(checks,indent=2))
    assert checks['question_quadrature_64_pass']


if __name__=='__main__':main()
