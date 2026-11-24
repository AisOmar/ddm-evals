"""Stable analytical symmetric DDM / normally varying drift likelihoods.

Same parameterisation as HSSM: boundaries +/-a, diffusion noise 1, z=.5.
The zero-drift Navarro--Fuss series is evaluated in log space without a
probability floor. Normal drift is integrated analytically in the density.
Survival integrates that density directly over (deadline, infinity), avoiding
subtraction of a near-one CDF and the external HSSM omission network.
"""
import numpy as np
import pytensor
import pytensor.tensor as pt
from numpy.polynomial.legendre import leggauss


def log_density(rt, response, v, a, t, sv=0.0):
    dt = pt.maximum(rt - t, 1e-12)
    tau = dt / (4 * a * a)
    # Lower-bound first-passage density with separation one, start .5.
    small_tau = pt.minimum(tau, .12)
    shifts = pt.as_tensor_variable(.5 + 2 * np.arange(-4, 5, dtype=float))
    small_sum = pt.sum(shifts * pt.exp(-(shifts**2 - .25) / (2 * small_tau[..., None])), axis=-1)
    small = pt.log(pt.maximum(small_sum, 1e-300)) - .5 * np.log(2 * np.pi) - 1.5 * pt.log(small_tau) - .125 / small_tau
    large_tau = pt.maximum(tau, .12)
    k = pt.as_tensor_variable(np.arange(1, 18, 2, dtype=float))
    signs = pt.as_tensor_variable((-1.0) ** np.arange(9))
    large_sum = pt.sum(k * signs * pt.exp(-(k**2 - 1) * np.pi**2 * large_tau[..., None] / 2), axis=-1)
    large = np.log(np.pi) + pt.log(pt.maximum(large_sum, 1e-300)) - np.pi**2 * large_tau / 2
    base = pt.switch(tau < .12, small, large) - 2 * pt.log(2 * a)
    drift = (a*a*sv*sv + 2*response*a*v - v*v*dt) / (2*(1+sv*sv*dt)) - .5*pt.log1p(sv*sv*dt)
    return pt.switch(rt > t, base + drift, -np.inf)


def log_survival(deadline, v, a, t, sv=0.0, nodes=64):
    """Gauss--Legendre tail integration with a rational infinite-time map.

    Numerical accuracy is checked separately against series, quadrature and
    node doubling. This is a probability, so C <= t gives log survival zero.
    """
    x, weights = leggauss(nodes)
    u = pt.as_tensor_variable((x+1)/2)
    w = pt.as_tensor_variable(weights/2)
    start = pt.maximum(deadline-t, 0)
    scale = a*a / (1 + pt.abs(v*a)/(1+sv*a))
    future = start[..., None] + scale[..., None]*u/(1-u)
    vv, aa, tt = v[..., None], a[..., None], t[..., None]
    ss = sv[..., None] if hasattr(sv, "ndim") and sv.ndim else sv
    lp_plus = log_density(future+tt, 1, vv, aa, tt, ss)
    lp_minus = log_density(future+tt, -1, vv, aa, tt, ss)
    integrand = pt.logaddexp(lp_plus, lp_minus) + pt.log(scale[..., None]) - 2*pt.log1p(-u) + pt.log(w)
    lp = pt.minimum(pt.logsumexp(integrand, axis=-1), 0)
    return pt.switch(deadline <= t, 0., lp)


def evaluate(rt, response, v, a, t, sv=0., censored=False, nodes=64):
    """Independent NumPy evaluation, chunked to bound predictive memory use."""
    from scipy.special import logsumexp
    def density(rr,resp,vv,aa,tt,ss):
        dt=np.maximum(rr-tt,1e-12);tau=dt/(4*aa*aa)
        st=np.minimum(tau,.12);lt=np.maximum(tau,.12)
        shifts=.5+2*np.arange(-4,5)
        sm=np.sum(shifts*np.exp(-(shifts**2-.25)/(2*st[...,None])),axis=-1)
        small=np.log(np.maximum(sm,1e-300))-.5*np.log(2*np.pi)-1.5*np.log(st)-.125/st
        k=np.arange(1,18,2);signs=(-1.)**np.arange(9)
        lm=np.sum(k*signs*np.exp(-(k*k-1)*np.pi**2*lt[...,None]/2),axis=-1)
        large=np.log(np.pi)+np.log(np.maximum(lm,1e-300))-np.pi**2*lt/2
        base=np.where(tau<.12,small,large)-2*np.log(2*aa)
        drift=(aa*aa*ss*ss+2*resp*aa*vv-vv*vv*dt)/(2*(1+ss*ss*dt))-.5*np.log1p(ss*ss*dt)
        return np.where(rr>tt,base+drift,-np.inf)
    vals = np.broadcast_arrays(*[np.asarray(x, dtype=float) for x in [rt, response, v, a, t, sv]])
    shape = vals[0].shape
    flat=[x.reshape(-1) for x in vals];out=np.empty(flat[0].size)
    batch=512 if censored else 20000
    if censored:
        x,w=leggauss(nodes);u=(x+1)/2;w=w/2
    for start in range(0,len(out),batch):
        rr,resp,vv,aa,tt,ss=[x[start:start+batch] for x in flat]
        if not censored:out[start:start+batch]=density(rr,resp,vv,aa,tt,ss)
        else:
            scale=aa*aa/(1+np.abs(vv*aa)/(1+ss*aa));future=np.maximum(rr-tt,0)[:,None]+scale[:,None]*u/(1-u)
            args=[x[:,None] for x in [vv,aa,tt,ss]]
            lp=np.logaddexp(density(future+tt[:,None],1,*args),density(future+tt[:,None],-1,*args))
            integrand=lp+np.log(scale[:,None])-2*np.log1p(-u)+np.log(w)
            result=np.minimum(logsumexp(integrand,axis=-1),0)
            out[start:start+batch]=np.where(rr<=tt,0,result)
    return out.reshape(shape)
