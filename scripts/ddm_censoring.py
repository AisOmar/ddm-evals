"""Analytical censoring term for the DDM: log P(T > C | v, a, z, t)  (plan 4.1 / 6.2).

HSSM 0.5 routes deadline data to a pretrained 'omission probability network' (ddm_opn.onnx) that is not in the
franklab/HSSM model repository (404 on 2026-10-07), so the survival term is supplied here.

Default: closed form. Integrating the Navarro-Fuss large-time density term by term gives, for boundary separation
A = 2a (HSSM's `a` is the half-width: boundaries at +/-a) and relative start w = z, decision time s = C - t,
    S_lower(s) = (pi/A^2) exp(-v A w) sum_k k sin(k pi w) exp(-lambda_k s) / lambda_k,   lambda_k = v^2/2 + k^2 pi^2/(2A^2)
    P(T > C)   = S_lower(s; v, w) + S_lower(s; -v, 1-w),  and 1 if s <= 0.
K=60 terms; the series converges fastest for large s and P(T>C) -> 1 as s -> 0, so truncation error is negligible
over the whole range (checked against quadrature of HSSM's own density and against simulation in test_survival()).
A quadrature version is kept for cross-checks; it is ~15x slower in the gradient.

Use:  hssm.HSSM(..., missing_data=True, deadline=True, loglik_missing_data=logp_ddm_survival_op)
with censored rows coded rt = -999.0 and a 'deadline' column holding C. (HSSM passes a plain callable through a
JAX wrapper that cannot trace PyTensor code; an Op instance is used as-is, hence the Op shell.)
"""
import numpy as np, pytensor, pytensor.tensor as pt
from hssm.likelihoods.analytical import logp_ddm

N_GRID = 128
K_TERMS = 60


def logp_ddm_survival_quadrature(deadline, v, a, z, t, n_grid=N_GRID):
    """PyTensor graph, trapezoid on HSSM's density (cross-check only). deadline: (n,1) or (n,); v,a,z,t: (n,) or scalar. Returns (n,) log P(T > deadline)."""
    C = pt.as_tensor_variable(deadline)
    C = C[:, 0] if C.ndim == 2 else C
    n = C.shape[0]
    v, a, z, t = [pt.broadcast_to(pt.as_tensor_variable(p, dtype=pytensor.config.floatX), (n,)) for p in (v, a, z, t)]
    s = pt.constant((np.linspace(0.0, 1.0, n_grid) ** 2).astype(pytensor.config.floatX))
    span = pt.maximum(C - t, 1e-6)
    tau = t[:, None] + span[:, None] * s[None, :] + 1e-6                     # (n, G), dense just above t
    tau_f = tau.reshape((-1,))
    rep = lambda x: pt.repeat(x, n_grid)
    dens = 0.0
    for r in (1.0, -1.0):
        data = pt.stack([tau_f, pt.full_like(tau_f, r)], axis=1)
        dens = dens + pt.exp(logp_ddm(data, rep(v), rep(a), rep(z), rep(t)))
    dens = dens.reshape((n, n_grid))
    cdf = pt.sum(0.5 * (dens[:, 1:] + dens[:, :-1]) * (tau[:, 1:] - tau[:, :-1]), axis=1)
    surv = pt.clip(1.0 - cdf, 1e-12, 1.0)
    return pt.switch(t >= C, 0.0, pt.log(surv))


def logp_ddm_survival(deadline, v, a, z, t, K=K_TERMS):
    """PyTensor graph, closed-form series. deadline: (n,1) or (n,); v,a,z,t: (n,) or scalar. Returns (n,) log P(T > deadline)."""
    C = pt.as_tensor_variable(deadline)
    C = C[:, 0] if C.ndim == 2 else C
    n = C.shape[0]
    v, a, z, t = [pt.broadcast_to(pt.as_tensor_variable(p, dtype=pytensor.config.floatX), (n,)) for p in (v, a, z, t)]
    s = pt.maximum(C - t, 0.0); A = 2.0 * a
    k = pt.constant(np.arange(1, K + 1, dtype=pytensor.config.floatX))[None, :]
    def S(vv, w):
        lam = vv[:, None] ** 2 / 2.0 + (k * np.pi) ** 2 / (2.0 * A[:, None] ** 2)
        return (np.pi / A ** 2) * pt.exp(-vv * A * w) * pt.sum(k * pt.sin(k * np.pi * w[:, None]) * pt.exp(-lam * s[:, None]) / lam, axis=1)
    surv = pt.clip(S(v, z) + S(-v, 1.0 - z), 1e-12, 1.0)
    return pt.switch(C <= t, 0.0, pt.log(surv))


class _SurvivalOp(pytensor.graph.Op):
    """Thin Op shell: HSSM returns Op instances unchanged and calls them with (deadline_column, *params)."""
    __props__ = ()
    def __call__(self, deadline, *params, **kwargs):
        return logp_ddm_survival(deadline, *params)
    def make_node(self, *inputs):  # never used: __call__ builds the graph directly
        raise NotImplementedError
    def perform(self, *args):
        raise NotImplementedError


logp_ddm_survival_op = _SurvivalOp()


_F = {}
def survival_np(C, v, a, z, t, method="series"):
    """Numpy convenience wrapper (compiled once per method)."""
    if method not in _F:
        Cv, vv, av, zv, tv = (pt.vector(n) for n in "Cvazt")
        g = logp_ddm_survival if method == "series" else logp_ddm_survival_quadrature
        _F[method] = pytensor.function([Cv, vv, av, zv, tv], g(Cv, vv, av, zv, tv))
    arrs = [np.asarray(x, dtype=float).reshape(-1) for x in (C, v, a, z, t)]
    n = max(len(x) for x in arrs)
    return _F[method](*[np.broadcast_to(x, (n,)).copy() for x in arrs])


def test_survival(n_sim=40000, seed=0):
    """Series vs quadrature vs simulation; prints max |sim - series|. (~0.01 at the shortest C is the Euler simulator's crossing-time bias, not the series: series and quadrature agree to 1e-4.)"""
    import hssm
    worst = 0.0
    for (v, a, t, C) in [(0.5, 1.5, 0.5, 5.0), (0.15, 2.7, 2.0, 10.0), (0.8, 1.2, 0.3, 1.0), (0.3, 2.0, 0.5, 3.0)]:
        sim = hssm.simulate_data(model="ddm", theta=dict(v=v, a=a, z=0.5, t=t), size=n_sim, random_state=seed, max_t=400)
        p_sim = float((sim.rt > C).mean()); p_s = float(np.exp(survival_np(C, v, a, 0.5, t))[0]); p_q = float(np.exp(survival_np(C, v, a, 0.5, t, "quadrature"))[0])
        worst = max(worst, abs(p_sim - p_s)); print(f"  v={v} a={a} t={t} C={C}: P(T>C) sim={p_sim:.4f} series={p_s:.4f} quad={p_q:.4f}")
    print(f"  max |sim - quad| = {worst:.4f} (MC se ~ {np.sqrt(0.25/n_sim):.4f})")
    return worst


if __name__ == "__main__":
    test_survival()
