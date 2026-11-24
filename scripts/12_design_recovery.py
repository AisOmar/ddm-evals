"""Replicated, pilot-calibrated model recovery. Offline: never calls an API.

Fast screening uses question-marginal MAP with grouped three-fold prediction;
it is explicitly distinct from posterior-integrated Bayesian model comparison.
Independent datasets, paired caps, failures and inconclusive outcomes are kept.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/ddm-mpl')
os.environ.setdefault('JAX_ENABLE_X64','true')
import argparse, hashlib, json, pathlib, time
import numpy as np
import pandas as pd
import xarray as xr
from scipy.special import expit, logit
from scipy.stats import norm
from ssms.basic_simulators.simulator import simulator
import recovery_marginal as m
from design import correct_is_a

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'results/design_recovery'
SOURCE=ROOT/'results/robustness'
CONDITIONS=['plain_concise','plain_thorough','sbs_concise','sbs_thorough']
PROFILES=['ddm_calibrated','ddm_question_time','ddm_high_sdv',
          'baseline_calibrated','baseline_correlated','baseline_contaminated']
EXTENSIONS=['ddm_lognormal_questions','ddm_low_variation']
MODELS=['baseline','ddm_sdv_lapse']
SEED=20261009


def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')


def library():
    """Keep joint draws (and their centering constants) from five R1 CV fits."""
    raw=pd.read_csv(SOURCE/'pilot_r1_with_provider.csv')
    ids=np.array(sorted(raw.qid.unique()));np.random.default_rng(20261006).shuffle(ids)
    folds=np.array_split(ids,5);out={name:[] for name in MODELS};provenance=[]
    for name in MODELS:
        for fold in range(5):
            p=SOURCE/'posteriors'/f'main_fold{fold}_{name}.nc'
            posterior=xr.open_dataset(p,group='posterior').stack(sample=('chain','draw'))
            def get(k):
                a=posterior[k];dims=[d for d in a.dims if d!='sample']
                return a.transpose('sample',*dims).values
            if name=='baseline':
                theta=np.column_stack([get('alpha'),np.log(get('sigma')),get('gamma_len'),np.log(get('tau_u')),
                                       get('beta'),get('gamma_acc'),get('beta_len'),np.log(get('tau_b'))])
                train=raw[~raw.qid.isin(folds[fold])]
                answered=train[(train.outcome=='answered')&(train.reasoning_tokens<=8192)]
                centre=float(np.log(answered.reasoning_tokens/100).mean())
            else:
                theta=np.column_stack([get('v_coefs'),get('a_coefs'),get('t_coefs'),np.log(get('tau_v')),
                                       get('sv_coefs'),logit(get('epsilon'))]);centre=0.
            out[name].append((theta,centre));posterior.close()
            provenance.append(dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return out,provenance,float(raw.drop_duplicates('qid').has_code.mean())


def plan(args):
    OUT.mkdir(parents=True,exist_ok=True)
    lib,provenance,code_rate=library()
    spec=dict(seed=SEED,questions=args.questions,conditions=CONDITIONS,repeats=2,folds=3,
              replicates=args.replicates,profiles=PROFILES,caps_tokens=[32768,8192],code_prevalence=code_rate,
              generators='Joint hyperparameter draws sampled uniformly from five R1 CV posterior fits; fresh question effects and trials per replicate.',
              stresses=dict(ddm_question_time='Add independent question timing: median 150 prose / 750 code tokens, log SD 0.7; 3.75% independent early termination with uniform 10%-90% cap deadline.',
                            ddm_high_sdv='Multiply within-question drift SD by 4.',
                            baseline_correlated='Correlation +0.6 between question length and accuracy effects.',
                            baseline_contaminated='Replace 8% of trials with fair-answer lognormal lengths (median 2000 tokens, log SD 2).'),
              option_position='Two A/two B conditions per question per repeat, reversed on repeat two; no simulated position effect.',
              primary='Joint held-out-question log predictive density; three grouped folds; question-cluster SE; abs(delta)>2*SE for a winner.',
              screening='Population MAP with question effects integrated by adaptive piecewise Legendre quadrature (DDM) / 64-node adaptive Gaussian quadrature (baseline); point hyperparameter prediction. NOT full Bayesian power.',
              settings=dict(question_nodes=args.nodes,baseline_nodes=64,tail_nodes=64,maxiter=350,starts=2),
              uncertainty='95% Wilson intervals across independent datasets; caps are paired. Invalid optimizations counted as failures.',
              readiness='Screening target: correct decisive selection >=80% in both calibrated model families, wrong decisive selection <=5%; stresses reported separately. Finite-replicate intervals and Bayesian confirmation constrain conclusions.',
              bayesian_confirmation='First replicate at 32768 for ddm_calibrated and baseline_calibrated, selected before outcome inspection; same three grouped folds.',
              source_artifacts=provenance)
    path=OUT/'plan.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old!=spec:raise ValueError('Plan already frozen with different settings. Use the recorded settings.')
    else:dump(path,spec)
    initials={name:np.median(np.concatenate([x for x,_ in lib[name]]),axis=0) for name in MODELS}
    return spec,lib,initials


def generate(profile,rep,spec,lib):
    case=f'{profile}_{rep:02d}';path=OUT/'data'/f'{case}.csv'
    if path.exists():return pd.read_csv(path)
    index=(PROFILES+EXTENSIONS).index(profile);seed=SEED+10000*index+rep
    rng=np.random.default_rng(seed);name=MODELS[profile.startswith('ddm')]
    fold=int(rng.integers(5));draw=int(rng.integers(len(lib[name][fold][0])))
    theta,centre=lib[name][fold];theta=theta[draw];P={k:np.asarray(v) for k,v in m.unpack(theta,name).items()}
    nq=spec['questions'];code_q=rng.random(nq)<spec['code_prevalence'];rows=[]
    for qi in range(nq):
        qid=f'q{qi:04d}'
        for ci,condition in enumerate(CONDITIONS):
            for repi in range(2):
                rows.append(dict(qid=qid,condition=condition,ci=ci,rep=repi,has_code=int(code_q[qi]),
                                 scaffold='step_by_step' if ci>=2 else 'plain',instruction='thorough' if ci%2 else 'concise',
                                 correct_is_A=correct_is_a(qid,condition,repi,CONDITIONS,seed),provider='simulation'))
    d=pd.DataFrame(rows);code=d.has_code.to_numpy();ci=d.ci.to_numpy()
    X=np.column_stack([np.ones(len(d)),ci>=2,ci%2,(ci>=2)*(ci%2),code])
    if name=='ddm_sdv_lapse':
        uq=rng.normal(0,.08 if profile=='ddm_low_variation' else P['tau_v'],nq)
        u=np.repeat(uq,8);v=X@P['v']+u
        if profile=='ddm_lognormal_questions':
            ref=np.maximum(P['v'][0]+P['v'][4]*code_q,.05)
            logsd=np.sqrt(np.log1p((P['tau_v']/ref)**2))
            z=uq/P['tau_v']
            multiplier=np.exp(logsd*z-.5*logsd**2)
            v=np.maximum(X@P['v'],.05)*np.repeat(multiplier,8)
        sv=np.exp(P['sv'][0]+code*P['sv'][1])*(4 if profile=='ddm_high_sdv' else 1)
        if profile=='ddm_low_variation':sv=np.zeros(len(d))
        a=np.exp(X@P['a']);t=np.exp(X@P['t'])
        if profile=='ddm_question_time':
            t+=np.repeat(rng.lognormal(np.log(1.5),.7,nq),8)*np.where(code,5,1)
        actual_v=v+rng.normal(size=len(d))*sv
        sim=simulator(np.column_stack([actual_v,a,np.full(len(d),.5),t]).astype('float32'),
                      model='ddm',n_samples=1,delta_t=.005,max_t=327.68,smooth_unif=False,random_state=seed)
        rt=sim['rts'].ravel().astype(float);correct=(sim['choices'].ravel()>0).astype(float)
        # SSMS uses a negative sentinel when the path fails to cross by max_t.
        rt[rt<0]=np.inf
        contaminated=rng.random(len(d))<(0 if profile=='ddm_low_variation' else P['epsilon'])
    else:
        z=rng.normal(size=(nq,2));uq=P['tau_u']*z[:,0]
        rho=.6 if profile=='baseline_correlated' else 0.
        bq=P['tau_b']*(rho*z[:,0]+np.sqrt(1-rho*rho)*z[:,1])
        logrt=P['alpha'][ci]+P['gamma_len']*code+np.repeat(uq,8)+P['sigma'][ci]*rng.normal(size=len(d))
        rt=np.exp(logrt)
        eta=P['beta'][ci]+P['gamma_acc']*code+np.repeat(bq,8)+P['beta_len']*(logrt-centre)
        correct=(rng.random(len(d))<expit(eta)).astype(float)
        contaminated=rng.random(len(d))<(.08 if profile=='baseline_contaminated' else 0.)
    rt[contaminated]=rng.lognormal(np.log(20),2,contaminated.sum())
    correct[contaminated]=rng.integers(2,size=contaminated.sum())
    # Early termination is an independent random censoring deadline, not an error.
    early=rng.random(len(d))<(.0375 if profile=='ddm_question_time' else 0.)
    d['latent_rt']=rt;d['latent_correct']=correct;d['early_fraction']=np.where(early,rng.uniform(.1,.9,len(d)),1.)
    d['contaminated']=contaminated
    path.parent.mkdir(parents=True,exist_ok=True);d.to_csv(path,index=False)
    overrides={}
    if profile=='ddm_low_variation':overrides=dict(tau_v=.08,sv=0.,epsilon=0.)
    if profile=='ddm_lognormal_questions':overrides=dict(question_drift='Moment-matched multiplicative lognormal, code-specific log SD; conditional mean drift floored at 0.05 before multiplication.')
    dump(path.with_suffix('.json'),dict(profile=profile,replicate=rep,seed=seed,posterior_fold=fold,posterior_draw=draw,
                                     generator=name,theta=theta.tolist(),baseline_centre=centre,overrides=overrides))
    return d


def censor(d,cap):
    d=d.copy();deadline=cap/100*d.early_fraction.to_numpy()
    d['censored']=d.latent_rt>=deadline;d['rt']=np.minimum(d.latent_rt,deadline)
    d['dl']=np.where(d.censored,deadline,np.nan)
    d['correct']=np.where(d.censored,np.nan,d.latent_correct)
    d['response']=np.where(d.correct==1,1,-1)
    d['outcome']=np.where(d.censored,np.where(d.early_fraction<1,'incomplete','censored'),'answered')
    return d


def screen_case(d,case,initials,args):
    path=OUT/'scores'/f'{case}.csv';diagpath=OUT/'fits'/f'{case}.json'
    if path.exists() and diagpath.exists():
        if all(x.get('fit_version') in [3,4] for x in json.loads(diagpath.read_text())):return
    ids=np.array(sorted(d.qid.unique()));np.random.default_rng(SEED).shuffle(ids)
    folds=np.array_split(ids,3);pieces=[];diags=[]
    for fold,held in enumerate(folds):
        train=ids[~np.isin(ids,held)]
        _,ordered=m.prepare(d,train);test=ordered[ordered.qid.isin(held)].copy()
        for name in MODELS:
            cache=OUT/'fits'/f'{case}_fold{fold}_{name}.json'
            record=json.loads(cache.read_text()) if cache.exists() else {}
            if record.get('fit_version') in [3,4]:theta=np.asarray(record['theta'])
            else:
                start=time.time();results=[]
                for attempt in range(2):
                    x=initials[name].copy()
                    if attempt:
                        rng=np.random.default_rng(SEED+fold);x+=rng.normal(0,.12,len(x))
                    result,data=m.fit(d,train,name,x,qnodes=args.nodes)
                    results.append(result)
                finite=[r for r in results if np.isfinite(r.fun) and np.isfinite(r.jac).all()]
                if not finite:raise RuntimeError(f'Nonfinite fits: {case}, {fold}, {name}')
                best=min(finite,key=lambda r:r.fun);theta=best.x
                # Check against 16-node integration at the fitted parameters.
                data,_=m.prepare(d[d.qid.isin(train)],train)
                fref=m.objective(name,max(16,args.nodes),64)
                refval,_=fref(theta,data)
                quadrature_error=float(refval)-float(best.fun)
                used_nodes=args.nodes
                if abs(quadrature_error)>2.:
                    refined,_=m.fit(d,train,name,theta,qnodes=16)
                    if np.isfinite(refined.fun):best=refined;theta=best.x;used_nodes=16
                    highval,_=m.objective(name,32,64)(theta,data)
                    quadrature_error=float(highval)-float(best.fun)
                # A second independently initialized fit must reach the same basin.
                spread=max(r.fun for r in finite)-best.fun
                record=dict(fit_version=4,quadrature_nodes=used_nodes,quadrature_error=quadrature_error,model=name,fold=fold,theta=theta.tolist(),objective=float(best.fun),
                            convergence=bool(best.success),gradient_max=float(np.abs(best.jac).max()),
                            start_objective_spread=float(spread),iterations=int(best.nit),seconds=time.time()-start,
                            valid=bool(best.success and np.abs(best.jac).max()<.5 and spread<2. and abs(quadrature_error)<2.))
                dump(cache,record)
            data,_=m.prepare(d,train);pred=m.point_predict(theta,name,data)
            mask=ordered.qid.isin(held).to_numpy()
            for component,score in pred.items():test[f'lpd_{name}_{component}']=score[mask]
            diags.append(record)
        test['fold']=fold;pieces.append(test)
    path.parent.mkdir(parents=True,exist_ok=True);pd.concat(pieces).to_csv(path,index=False)
    dump(diagpath,diags)


def wilson(k,n):
    if not n:return [None,None]
    z=norm.ppf(.975);p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,mid-half),min(1,mid+half)]


def summarize(spec):
    rows=[];profiles=[]
    for profile in PROFILES:
        truth='ddm' if profile.startswith('ddm') else 'baseline'
        for rep in range(spec['replicates']):
            for cap in spec['caps_tokens']:
                case=f'{profile}_{rep:02d}_cap{cap}';path=OUT/'scores'/f'{case}.csv'
                if not path.exists():continue
                d=pd.read_csv(path);diags=json.loads((OUT/'fits'/f'{case}.json').read_text())
                if not all(x.get('fit_version') in [3,4,5] for x in diags):continue
                valid=all(x['valid'] for x in diags)
                profiles.append(dict(case=case,answered=int((~d.censored).sum()),censored=int(d.censored.sum()),
                                     accuracy=float(d.loc[~d.censored,'correct'].mean()),median_observed_tokens=float(d.loc[~d.censored,'rt'].median()*100)))
                for comp in ['joint','length','correctness_given_length']:
                    diff=d[f'lpd_ddm_sdv_lapse_{comp}']-d[f'lpd_baseline_{comp}'];q=diff.groupby(d.qid).sum()
                    delta=float(q.sum());se=float(np.sqrt(len(q)*q.var(ddof=1)))
                    winner='ddm' if delta>2*se else 'baseline' if delta< -2*se else 'inconclusive'
                    if not valid:winner='fit failure'
                    rows.append(dict(case=case,profile=profile,replicate=rep,cap=cap,truth=truth,component=comp,
                                     delta=delta,se=se,winner=winner,correct_decisive=winner==truth,
                                     wrong_decisive=winner in ['ddm','baseline'] and winner!=truth,valid=valid))
    pd.DataFrame(rows).to_csv(OUT/'comparisons.csv',index=False)
    pd.DataFrame(profiles).to_csv(OUT/'data_profiles.csv',index=False)
    result=[]
    if rows:
        joint=pd.DataFrame(rows).query('component=="joint"')
        for (profile,cap),group in joint.groupby(['profile','cap']):
            n=len(group);k=int(group.correct_decisive.sum());wrong=int(group.wrong_decisive.sum())
            result.append(dict(profile=profile,cap=int(cap),n=n,correct=k,wrong=wrong,
                               inconclusive=int((group.winner=='inconclusive').sum()),failures=int((group.winner=='fit failure').sum()),
                               correct_ci=wilson(k,n),wrong_ci=wilson(wrong,n)))
    dump(OUT/'recovery_rates.json',result)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['plan','generate','screen','summarize','bayes'],default='screen')
    ap.add_argument('--replicates',type=int,default=20);ap.add_argument('--questions',type=int,default=400)
    ap.add_argument('--nodes',type=int,default=4);ap.add_argument('--profile',choices=PROFILES+EXTENSIONS);ap.add_argument('--rep',type=int)
    args=ap.parse_args();spec,lib,initials=plan(args)
    if args.stage=='plan':return
    if args.stage=='summarize':summarize(spec);return
    for profile in ([args.profile] if args.profile else PROFILES):
        for rep in ([args.rep] if args.rep is not None else range(args.replicates)):
            d=generate(profile,rep,spec,lib)
            if args.stage=='generate':continue
            for cap in spec['caps_tokens']:
                case=f'{profile}_{rep:02d}_cap{cap}'
                if args.stage=='screen':
                    print(f'Screen {case}',flush=True);screen_case(censor(d,cap),case,initials,args);summarize(spec)
                elif args.stage=='bayes':
                    if cap!=32768 or rep!=0 or profile not in ['ddm_calibrated','baseline_calibrated']:continue
                    import importlib.util
                    module=importlib.util.spec_from_file_location('robustness',ROOT/'scripts/08_robustness.py')
                    r=importlib.util.module_from_spec(module);module.loader.exec_module(r)
                    r.OUT=OUT/'bayesian';r.OUT.mkdir(exist_ok=True);(r.OUT/'posteriors').mkdir(exist_ok=True)
                    r.SEED=SEED
                    from types import SimpleNamespace
                    a=SimpleNamespace(draws=500,tune=1000,chains=2,target_accept=.97,dense_mass=False,centered_effects=True,analytic_prediction=True)
                    # Reuse the same posterior checkpoints but write analytically
                    # integrated scores separately from the historical MC scores.
                    fit_original=r.fit_model
                    def fit_reuse(train,name,label,args,provider_adjust=False):
                        return fit_original(train,name,label.replace('_analytic',''),args,provider_adjust)
                    r.fit_model=fit_reuse
                    r.cv(censor(d,cap),case+"_centered_analytic",MODELS,a,k=3)


if __name__=='__main__':main()
