"""Fast population-parameter fits for replicated model-recovery screening.

Question effects are integrated out, rather than jointly MAP-estimated (which
would distort variance estimates). Uses piecewise Legendre quadrature with
adaptive intervals for the DDM, exact Gaussian conditioning for baseline
length, and adaptive quadrature for baseline correctness. Hyperparameters use
those of 08, with transformed priors. Predictions integrate population effects.
This is a screening approximation, not a replacement for Bayesian CV.
"""
import os
os.environ.setdefault('JAX_ENABLE_X64','true')
import jax
jax.config.update('jax_enable_x64',True)
import jax.numpy as j
import jax.scipy.special as js
import numpy as np
from numpy.polynomial.hermite import hermgauss
from numpy.polynomial.legendre import leggauss
from scipy.optimize import minimize
from scipy.special import logsumexp,expit
from scipy.stats import norm

LOG2PI=np.log(2*np.pi)


def gaussian_nodes(n):
    x,w=hermgauss(n)
    return j.asarray(np.sqrt(2)*x),j.asarray(np.log(w/np.sqrt(np.pi)))


def normal_sf(z):
    return js.log_ndtr(-z)


def zero_density(dt,a):
    dt=j.maximum(dt,1e-12);tau=dt/(4*a*a)
    st=j.minimum(tau,.12);lt=j.maximum(tau,.12)
    shifts=j.asarray(.5+2*np.arange(-4,5))
    sm=j.sum(shifts*j.exp(-(shifts**2-.25)/(2*st[...,None])),axis=-1)
    small=j.log(j.maximum(sm,1e-300))-.5*LOG2PI-1.5*j.log(st)-.125/st
    k=j.asarray(np.arange(1,18,2));signs=j.asarray((-1.)**np.arange(9))
    lm=j.sum(k*signs*j.exp(-(k*k-1)*np.pi**2*lt[...,None]/2),axis=-1)
    large=np.log(np.pi)+j.log(j.maximum(lm,1e-300))-np.pi**2*lt/2
    return j.where(tau<.12,small,large)-2*j.log(2*a)


def density(rt,r,v,a,t,sv):
    dt=j.maximum(rt-t,1e-12);den=1+sv*sv*dt
    drift=(a*a*sv*sv+2*r*a*v-v*v*dt)/(2*den)-.5*j.log(den)
    return j.where(rt>t,zero_density(dt,a)+drift,-j.inf)


def survival_shared(C,v,a,t,sv,mean_v,nodes=64):
    """Shared integration mesh across question-effect proposals; validated later.

    v has shape (censored slots, effect nodes), other arrays (slots,).
    """
    x,w=leggauss(nodes);u=j.asarray((x+1)/2);lw=j.asarray(np.log(w/2))
    start=j.maximum(C-t,0)
    scale=a*a/(1+j.abs(mean_v*a)/(1+sv*a))
    dt=start[:,None]+scale[:,None]*u/(1-u)
    base=zero_density(dt,a[:,None])
    D=1+sv[:,None]**2*dt
    av=a[:,None,None]*v[:,:,None]/D[:,None,:]
    drift=(a[:,None,None]**2*sv[:,None,None]**2-v[:,:,None]**2*dt[:,None,:])/(2*D[:,None,:])-.5*j.log(D[:,None,:])
    lp=base[:,None,:]+drift+j.logaddexp(av,-av)+j.log(scale[:,None,None])-2*j.log1p(-u)+lw
    result=j.minimum(js.logsumexp(lp,axis=-1),0)
    return j.where(C[:,None]<=t[:,None],0.,result)


def unpack(theta,name):
    if name=='baseline':
        return dict(alpha=theta[:4],sigma=j.exp(theta[4:8]),gamma_len=theta[8],tau_u=j.exp(theta[9]),
                    beta=theta[10:14],gamma_acc=theta[14],beta_len=theta[15],tau_b=j.exp(theta[16]))
    return dict(v=theta[:5],a=theta[5:10],t=theta[10:15],tau_v=j.exp(theta[15]),sv=theta[16:18],epsilon=js.expit(theta[18]))


def prior(theta,name):
    if name=='baseline':
        P=unpack(theta,name)
        return (-.5*j.sum(((P['alpha']-1)/2)**2)-.5*j.sum(((P['beta']-1)/2)**2)
                -.5*j.sum((theta[j.asarray([8,14,15])]/1.5)**2)
                +j.sum(theta[4:8])-.5*j.sum(P['sigma']**2)+theta[9]-.5*P['tau_u']**2
                +theta[16]-.5*(P['tau_b']/1.5)**2)
    P=unpack(theta,name);vmean=j.asarray([.4,0,0,0,0]);amean=j.asarray([np.log(4),0,0,0,0]);tmean=j.asarray([np.log(.5),0,0,0,0])
    return (-.5*j.sum(((P['v']-vmean)/.6)**2)-.5*j.sum(((P['a']-amean)/.7)**2)
            -.5*j.sum(((P['t']-tmean)/.8)**2)+theta[15]-.5*(P['tau_v']/.5)**2
            -.5*j.sum(((P['sv']-j.asarray([np.log(.4),0]))/.8)**2)
            -jax.nn.softplus(-theta[18])-19*jax.nn.softplus(theta[18]))


def question_logp(theta,name,d,qnodes=16,tailnodes=64):
    P=unpack(theta,name);rt=d['rt'];y=d['y'];c=d['cens'];code=d['code'];ci=d['ci'];X=d['X']
    zn,lw=gaussian_nodes(64);obs=(~c).astype(float)
    if name=='baseline':
        lrt=j.log(rt);mu=P['alpha'][ci]+P['gamma_len']*code;sd=P['sigma'][ci]
        residual=lrt-mu;weights=obs/sd**2
        V=1/(1/P['tau_u']**2+j.sum(weights,axis=1));H=j.sum(weights*residual,axis=1)
        m=V*H
        # Integral of all answered Gaussian densities, including RT Jacobians.
        length=-.5*j.sum(obs*(LOG2PI+2*j.log(sd)+residual**2/sd**2),axis=1)
        length+=.5*j.log(V/P['tau_u']**2)+.5*V*H**2-j.sum(obs*lrt,axis=1)
        u=m[:,None]+j.sqrt(V[:,None])*zn
        lp=normal_sf((lrt[:,:,None]-mu[:,:,None]-u[:,None,:])/sd[:,:,None])
        length+=js.logsumexp(lw+j.sum(j.where(c[:,:,None],lp,0),axis=1),axis=1)
        eta=P['beta'][ci]+P['gamma_acc']*code+P['beta_len']*(lrt-d['centre'])
        b=j.zeros(rt.shape[0])
        for _ in range(8):
            prob=js.expit(eta+b[:,None]);g=j.sum(obs*(y-prob),axis=1)-b/P['tau_b']**2
            h=j.sum(obs*prob*(1-prob),axis=1)+1/P['tau_b']**2
            b=b+j.clip(g/h,-2,2)
        prob=js.expit(eta+b[:,None]);h=j.sum(obs*prob*(1-prob),axis=1)+1/P['tau_b']**2
        sb=1/j.sqrt(h);xx=b[:,None]+sb[:,None]*zn
        ee=eta[:,:,None]+xx[:,None,:]
        acc=j.sum(obs[:,:,None]*(y[:,:,None]*ee-jax.nn.softplus(ee)),axis=1)
        log_prior=-.5*(xx/P['tau_b'])**2-j.log(P['tau_b'])-.5*LOG2PI
        log_proposal=-.5*zn**2-j.log(sb[:,None])-.5*LOG2PI
        acc=js.logsumexp(lw+acc+log_prior-log_proposal,axis=1)
        return length+acc
    mean_v=X@P['v'];a=j.exp(X@P['a']);t=j.exp(X@P['t']);sv=j.exp(P['sv'][0]+code*P['sv'][1])
    dt=j.maximum(rt-t,1e-12);den=1+sv**2*dt
    W=dt/den;L=(2*y-1)*a/den-W*mean_v
    usable=(~c)
    # All crossings, correct crossings, incorrect crossings, and the prior.
    masks=j.stack([usable,usable&(y==1),usable&(y==0),j.zeros_like(usable)],axis=1)
    V=1/(1/P['tau_v']**2+j.sum(masks*W[:,None,:],axis=2))
    m=V*j.sum(masks*L[:,None,:],axis=2)
    # Long censored trials concentrate around zero drift. A prior-only mesh
    # misses that narrow mode; add censor-conditioned and combined proposals.
    wc=j.where(c,W,0);lc=-wc*mean_v
    for include_answers in [False,True]:
        ww=wc+j.where(usable,W,0)*float(include_answers)
        ll=lc+j.where(usable,L,0)*float(include_answers)
        vv=1/(1/P['tau_v']**2+j.sum(ww,axis=1))
        mm=vv*j.sum(ll,axis=1)
        V=j.concatenate([V,vv[:,None]],axis=1);m=j.concatenate([m,mm[:,None]],axis=1)
    # Piecewise Legendre integration over the prior, with breakpoints around
    # candidate modes. Unlike importance-mixture GH, this does not double count
    # narrow modes when a coarse prior grid happens to land on them.
    spans=j.asarray([-6.,-2.,0.,2.,6.])
    knots=(m[:,:,None]+j.sqrt(V[:,:,None])*spans).reshape(rt.shape[0],-1)
    limit=10*P['tau_v']
    knots=j.clip(knots,-limit,limit)
    knots=j.sort(j.concatenate([j.full((rt.shape[0],1),-limit),knots,j.full((rt.shape[0],1),limit)],axis=1),axis=1)
    left=knots[:,:-1];width=j.maximum(knots[:,1:]-left,1e-12)
    nodes,weights=leggauss(qnodes)
    u=(left[:,:,None]+width[:,:,None]*j.asarray((nodes+1)/2)).reshape(rt.shape[0],-1)
    log_weights=(j.log(width[:,:,None])+j.asarray(np.log(weights/2))).reshape(rt.shape[0],-1)
    log_prior=-.5*(u/P['tau_v'])**2-j.log(P['tau_v'])-.5*LOG2PI
    v=mean_v[:,:,None]+u[:,None,:]
    lp=density(rt[:,:,None],(2*y-1)[:,:,None],v,a[:,:,None],t[:,:,None],sv[:,:,None])
    flat=d['cindex'];valid=d['cvalid']
    fq=flat//rt.shape[1];fr=flat%rt.shape[1]
    cs=survival_shared(rt[fq,fr],v[fq,fr,:],a[fq,fr],t[fq,fr],sv[fq,fr],mean_v[fq,fr],tailnodes)
    # Padded duplicate indices must add zero, rather than overwrite real rows.
    lp=j.where(c[:,:,None],0,lp)
    lp=lp.at[fq,fr,:].add(j.where(valid[:,None],cs,0))
    e=P['epsilon']
    contam=j.where(c,normal_sf((j.log(rt)-np.log(20))/2),norm_constant(rt)-np.log(2))
    lp=j.logaddexp(j.log1p(-e)+lp,j.log(e)+contam[:,:,None])
    joint=j.sum(lp,axis=1)+log_prior
    return js.logsumexp(joint+log_weights,axis=1)


def norm_constant(rt):
    return -.5*((j.log(rt)-np.log(20))/2)**2-np.log(2)-.5*LOG2PI-j.log(rt)


FUNCS={}
def objective(name,qnodes=16,tailnodes=64):
    key=(name,qnodes,tailnodes)
    if key not in FUNCS:
        def loss(theta,d):return -j.sum(d['train']*question_logp(theta,name,d,qnodes,tailnodes))-prior(theta,name)
        FUNCS[key]=jax.jit(jax.value_and_grad(loss))
    return FUNCS[key]


def composite_question_logp(theta,name,d):
    """Composite likelihood of trial marginals; dependence remains in the data.

    This optimizes the marginal predictive family used for held-out trial scores,
    but discards within-question covariance during fitting. It cannot recover
    the split of trial and question variance. Use only for replicated screening,
    with hierarchical-fit confirmation, never as Bayesian power or recovery.
    """
    P=unpack(theta,name);rt=d['rt'];y=d['y'];c=d['cens'];code=d['code'];ci=d['ci'];X=d['X']
    if name=='baseline':
        mu=P['alpha'][ci]+P['gamma_len']*code;sd=j.sqrt(P['sigma'][ci]**2+P['tau_u']**2)
        length=j.where(c,normal_sf((j.log(rt)-mu)/sd),-.5*((j.log(rt)-mu)/sd)**2-j.log(sd)-.5*LOG2PI-j.log(rt))
        z,lw=gaussian_nodes(64)
        eta=P['beta'][ci]+P['gamma_acc']*code+P['beta_len']*(j.log(rt)-d['centre'])
        ee=eta[:,:,None]+P['tau_b']*z
        logp=js.logsumexp(-jax.nn.softplus(-ee)+lw,axis=-1)
        log1p=js.logsumexp(-jax.nn.softplus(ee)+lw,axis=-1)
        return j.sum(length+j.where(c,0,j.where(y==1,logp,log1p)),axis=1)
    v=X@P['v'];a=j.exp(X@P['a']);t=j.exp(X@P['t'])
    sv=j.sqrt(j.exp(P['sv'][0]+code*P['sv'][1])**2+P['tau_v']**2)
    lp=density(rt,2*y-1,v,a,t,sv)
    flat=d['cindex'];fq=flat//8;fr=flat%8
    cs=survival_shared(rt[fq,fr],v[fq,fr,None],a[fq,fr],t[fq,fr],sv[fq,fr],v[fq,fr],128)[:,0]
    lp=j.where(c,0,lp).at[fq,fr].add(j.where(d['cvalid'],cs,0))
    cl=j.where(c,normal_sf((j.log(rt)-np.log(20))/2),norm_constant(rt)-np.log(2))
    e=P['epsilon'];return j.sum(j.logaddexp(j.log1p(-e)+lp,j.log(e)+cl),axis=1)


def composite_objective(name):
    key=('composite',name)
    if key not in FUNCS:
        def loss(theta,d):return -j.sum(d['train']*composite_question_logp(theta,name,d))-prior(theta,name)
        FUNCS[key]=jax.jit(jax.value_and_grad(loss))
    return FUNCS[key]


def prepare(frame,train_qids,cslots=None):
    frame=frame.sort_values(['qid','ci','rep']).copy();qids=frame.qid.unique();nq=len(qids)
    assert len(frame)==nq*8 and frame.groupby('qid').size().eq(8).all()
    rt=frame.rt.to_numpy().reshape(nq,8);c=frame.censored.to_numpy().reshape(nq,8)
    y=frame.correct.fillna(0).to_numpy(float).reshape(nq,8)
    s=frame.scaffold.isin(['step_by_step','sbs']).to_numpy(float);i=frame.instruction.eq('thorough').to_numpy(float);code=frame.has_code.to_numpy(float)
    X=np.column_stack([np.ones(len(frame)),s,i,s*i,code]).reshape(nq,8,5)
    train=np.isin(qids,train_qids)
    observed_train=rt[(~c)&train[:,None]]
    centre=float(np.log(observed_train).mean()) if len(observed_train) else 0.
    indices=np.flatnonzero(c)
    if cslots is None:cslots=max(32,2**int(np.ceil(np.log2(max(1,len(indices))))))
    assert len(indices)<=cslots,(len(indices),cslots)
    ci=np.zeros(cslots,dtype=int);ci[:len(indices)]=indices;cv=np.arange(cslots)<len(indices)
    return {k:j.asarray(v) for k,v in dict(rt=rt,y=y,cens=c,code=code.reshape(nq,8),ci=frame.ci.to_numpy().reshape(nq,8),X=X,train=train,centre=centre,cindex=ci,cvalid=cv).items()},frame


def fit(frame,train_qids,name,initial,qnodes=16,tailnodes=64,maxiter=350,method='hierarchical'):
    frame=frame[frame.qid.isin(train_qids)]
    d,_=prepare(frame,train_qids)
    f=composite_objective(name) if method=='composite' else objective(name,qnodes,tailnodes)
    def wrapped(theta):
        value,grad=f(j.asarray(theta),d);return float(value),np.asarray(grad)
    start=np.asarray(initial,float)
    bounds=[(-8,8)]*len(start)
    if name=='baseline':
        for idx in [4,5,6,7,9,16]:bounds[idx]=(-5,2)
    else:
        bounds[15]=(-5,2);bounds[16]=(-6,1);bounds[18]=(-9,0)
    result=minimize(wrapped,start,jac=True,method='L-BFGS-B',bounds=bounds,
                    options=dict(maxiter=maxiter,ftol=1e-10,gtol=1e-4,maxls=40))
    return result,d


def point_predict(theta,name,d):
    """Exact population drift convolution; baseline logistic-normal quadrature."""
    from diffusion_likelihood import evaluate
    P={k:np.asarray(v) for k,v in unpack(j.asarray(theta),name).items()}
    rt=np.asarray(d['rt']).ravel();y=np.asarray(d['y']).ravel();c=np.asarray(d['cens']).ravel();code=np.asarray(d['code']).ravel();ci=np.asarray(d['ci']).ravel();X=np.asarray(d['X']).reshape(-1,5)
    if name=='baseline':
        mu=P['alpha'][ci]+P['gamma_len']*code;sd=np.sqrt(P['sigma'][ci]**2+P['tau_u']**2)
        length=np.where(c,norm.logsf((np.log(rt)-mu)/sd),norm.logpdf(np.log(rt),mu,sd)-np.log(rt))
        z,w=hermgauss(48);eta=P['beta'][ci]+P['gamma_acc']*code+P['beta_len']*(np.log(rt)-float(d['centre']))
        p=expit(eta[:,None]+np.sqrt(2)*P['tau_b']*z)@(w/np.sqrt(np.pi));p=np.clip(p,1e-15,1-1e-15)
        joint=length+np.where(c,0,np.where(y==1,np.log(p),np.log1p(-p)))
    else:
        v=X@P['v'];a=np.exp(X@P['a']);t=np.exp(X@P['t']);sv=np.sqrt(np.exp(P['sv'][0]+code*P['sv'][1])**2+P['tau_v']**2)
        lp=evaluate(rt,2*y-1,v,a,t,sv);other=evaluate(rt,1-2*y,v,a,t,sv)
        length=np.logaddexp(lp,other);joint=lp
        joint[c]=length[c]=evaluate(rt[c],0,v[c],a[c],t[c],sv[c],censored=True,nodes=128)
        cl=np.where(c,norm.logsf((np.log(rt)-np.log(20))/2),norm.logpdf(np.log(rt),np.log(20),2)-np.log(rt))
        joint=np.logaddexp(np.log1p(-P['epsilon'])+joint,np.log(P['epsilon'])+cl-np.where(c,0,np.log(2)))
        length=np.logaddexp(np.log1p(-P['epsilon'])+length,np.log(P['epsilon'])+cl)
    return dict(joint=joint,length=length,correctness_given_length=joint-length)


def posterior_predict_exact(P,test):
    """Integrate new-question Normal effects analytically, then posterior draws.

    For per-trial prediction, Normal question drift and Normal trial drift add
    in variance. Baseline length is also a Normal convolution; its independent
    accuracy effect needs only one-dimensional logistic-Normal quadrature.
    Question clustering is retained in comparison uncertainty, outside here.
    """
    from diffusion_likelihood import evaluate
    rt=test.rt.to_numpy()[:,None];y=test.correct.fillna(0).to_numpy()[:,None]
    c=test.censored.to_numpy();code=test.has_code.to_numpy()[:,None];ci=test.ci.to_numpy()
    if P['name']=='baseline':
        mu=P['alpha'][ci]+code*P['gamma_len'][None,:]
        sd=np.sqrt(P['sigma'][ci]**2+P['tau_u'][None,:]**2)
        length=np.where(c[:,None],norm.logsf((np.log(rt)-mu)/sd),norm.logpdf(np.log(rt),mu,sd)-np.log(rt))
        eta=P['beta'][ci]+code*P['gamma_acc'][None,:]+P['beta_len'][None,:]*(np.log(rt)-P['centre'])
        z,w=hermgauss(64);prob=np.zeros_like(eta)
        for i in range(0,len(test),32):
            prob[i:i+32]=expit(eta[i:i+32,:,None]+np.sqrt(2)*P['tau_b'][None,:,None]*z)@(w/np.sqrt(np.pi))
        prob=np.clip(prob,1e-15,1-1e-15)
        joint=length+np.where(c[:,None],0,np.where(y==1,np.log(prob),np.log1p(-prob)))
    else:
        ci=test.ci.to_numpy();X=np.column_stack([np.ones(len(test)),ci>=2,ci%2,(ci>=2)*(ci%2),code.ravel()])
        v=X@P['v_coefs'];a=np.exp(X@P['a_coefs']);t=np.exp(X@P['t_coefs'])
        sv=np.sqrt(np.exp(P['sv_coefs'][0][None,:]+code*P['sv_coefs'][1][None,:])**2+P['tau_v'][None,:]**2)
        joint=evaluate(rt,2*y-1,v,a,t,sv);other=evaluate(rt,1-2*y,v,a,t,sv)
        length=np.logaddexp(joint,other)
        surv=evaluate(rt[c],0,v[c],a[c],t[c],sv[c],censored=True,nodes=128)
        joint[c]=surv;length[c]=surv
        cl=np.where(c[:,None],norm.logsf((np.log(rt)-np.log(20))/2),norm.logpdf(np.log(rt),np.log(20),2)-np.log(rt))
        e=P['epsilon'][None,:]
        joint=np.logaddexp(np.log1p(-e)+joint,np.log(e)+cl-np.where(c[:,None],0,np.log(2)))
        length=np.logaddexp(np.log1p(-e)+length,np.log(e)+cl)
    S=length.shape[1];joint=logsumexp(joint,axis=1)-np.log(S);length=logsumexp(length,axis=1)-np.log(S)
    return dict(joint=joint,length=length,correctness_given_length=joint-length)
