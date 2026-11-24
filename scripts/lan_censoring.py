"""Censoring term for network (LAN) likelihoods: log P(T > C | params), by quadrature on the network density.

The closed-form survival in ddm_censoring.py holds for fixed bounds only. For a collapsing-bound model (angle) the
density is the LAN itself, so P(T > C) = 1 - sum_choices integral_t^C exp(LAN(rt, choice; params)) d rt, computed by
the trapezoid rule on a grid dense just above the non-decision time t. Written as a single-trial JAX function so HSSM
vectorises it the same way it vectorises the main LAN (jax backend, vmap over trials, params_is_reg).

Use:  hssm.HSSM(..., model="angle", missing_data=True, deadline=True, loglik_missing_data=make_lan_survival("angle"))
with censored rows coded rt = -999.0 and a 'deadline' column holding C, in the LAN's time units.
"""
import numpy as np, jax, jax.numpy as jnp
from huggingface_hub import hf_hub_download
from hssm.distribution_utils.onnx import load_onnx_model, make_jax_func

N_GRID = 96
T_MAX = 20.0    # the networks are trained on rt below ~20 time units; beyond that their output floors at exp(-16)


def lan_path(model):
    return hf_hub_download("franklab/HSSM", f"{model}.onnx")


def make_lan_survival(model, n_grid=N_GRID, floor=1e-12):
    """Single-trial callable surv(deadline, *params) -> log P(T > deadline). `deadline` arrives as a length-1 row
    (HSSM passes the deadline column of the missing rows); params are scalars after HSSM's vmap. The grid spacing is
    quadratic so it is dense where the density rises steeply just after t."""
    f = make_jax_func(load_onnx_model(lan_path(model)))
    s = jnp.asarray(np.linspace(0.0, 1.0, n_grid) ** 2)

    def surv(deadline, *params):
        C = jnp.reshape(deadline, ())
        t = params[3]                                   # list_params order: v, a, z, t, (theta ...)
        pv = jnp.asarray(params)
        # One grid from t to max(C, T_MAX); cumulative trapezoid gives the mass up to every node, the mass up to C
        # by linear interpolation, and the total mass at the last node. One network pass per row serves both.
        top = jnp.maximum(C, T_MAX)
        tau = t + jnp.maximum(top - t, 1e-6) * s + 1e-6

        def dens(rt):
            return sum(jnp.exp(f(jnp.concatenate((pv, jnp.array([rt, c]))))) for c in (1.0, -1.0))

        d = jax.vmap(dens)(tau)
        seg = 0.5 * (d[1:] + d[:-1]) * (tau[1:] - tau[:-1])
        cum = jnp.concatenate((jnp.zeros(1), jnp.cumsum(seg)))
        total = cum[-1]
        mass_C = jnp.interp(C, tau, cum)
        # The network density is not exactly normalised (total mass 0.98-1.02 for angle inside its training range,
        # up to 1.2 for the ddm network at slow drift), so the survival is taken relative to the total mass.
        return jnp.where(C <= t, 0.0, jnp.log(jnp.clip(1.0 - mass_C / total, floor, 1.0)))

    return surv


def survival_np(model, C, **theta):
    """Numpy convenience: P(T > C) for one parameter set."""
    f = make_lan_survival(model)
    names = {"angle": ["v", "a", "z", "t", "theta"], "ddm": ["v", "a", "z", "t"]}[model]
    return float(np.exp(f(jnp.array([C]), *[jnp.asarray(theta[n], dtype=float) for n in names])))


def test_survival(n_sim=40000, seed=0):
    """Quadrature on the LAN vs simulation from the generative model (ssm-simulators via hssm.simulate_data)."""
    import hssm
    worst = 0.0
    cases = [("angle", dict(v=0.5, a=1.5, z=0.5, t=0.3, theta=0.3), 2.0), ("angle", dict(v=0.2, a=2.5, z=0.5, t=0.5, theta=0.1), 6.0),
             ("angle", dict(v=1.0, a=1.0, z=0.5, t=0.2, theta=0.8), 1.0), ("angle", dict(v=0.3, a=2.0, z=0.5, t=1.0, theta=0.0), 8.0),
             ("angle", dict(v=0.3, a=2.8, z=0.5, t=1.0, theta=0.0), 12.0),   # near the a bound with rts beyond 20: the network itself is off here
             ("ddm", dict(v=0.5, a=1.5, z=0.5, t=0.3), 2.0), ("ddm", dict(v=0.2, a=2.5, z=0.5, t=0.5), 6.0)]
    for model, th, C in cases:
        sim = hssm.simulate_data(model=model, theta=th, size=n_sim, random_state=seed)
        p_sim = float((sim.rt > C).mean()); p_q = survival_np(model, C, **th)
        worst = max(worst, abs(p_sim - p_q)); print(f"  {model} {th} C={C}: P(T>C) sim={p_sim:.4f} quad={p_q:.4f}")
    print(f"  max |sim - quad| = {worst:.4f} (MC se ~ {np.sqrt(0.25/n_sim):.4f})")
    return worst


if __name__ == "__main__":
    test_survival()
