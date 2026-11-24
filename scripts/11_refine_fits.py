"""Refine selected diagnostic failures without discarding the original fits.

Uses the same model and data, with a larger sampling budget. Refined fits are
completed before replacing any checkpoint; original fits remain in an archive.
Run 08 --stage recovery after refining parameter recovery to refresh intervals,
and 08 --stage summarize after all refinements to refresh comparisons.
"""
import argparse
import importlib.util
import json
import re
import shutil
import time
from pathlib import Path
import numpy as np
import pandas as pd

spec=importlib.util.spec_from_file_location("robustness",Path(__file__).with_name("08_robustness.py"))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--labels",nargs="+",required=True)
    ap.add_argument("--draws",type=int,default=1000)
    ap.add_argument("--tune",type=int,default=2000)
    ap.add_argument("--chains",type=int,default=4)
    ap.add_argument("--target-accept",type=float,default=.995)
    ap.add_argument("--dense-mass",action="store_true")
    args=ap.parse_args()
    for label in args.labels:
        match=re.fullmatch(r"(main|exclude_incomplete|hidden_only|deepinfra|provider_adjusted)_(fold\d+|within)_(baseline|ddm_lapse|ddm_sdv_lapse)",label)
        if match:
            scenario,split,name=match.groups();d=r.data(scenario)
            if split=="within":train=d[d.rep%2==0];k=5
            else:
                k=5 if scenario=="main" else 3
                ids=np.array(sorted(d.qid.unique()));np.random.default_rng(r.SEED).shuffle(ids)
                heldout=np.array_split(ids,k)[int(split.removeprefix("fold"))]
                train=d[~d.qid.isin(heldout)]
            provider_adjust=scenario=="provider_adjusted"
        elif re.fullmatch(r"recovery400_(drift|boundary)_\d+",label):
            train=pd.read_csv(r.OUT/f"{label}.csv");name="ddm_sdv_tq_lapse";provider_adjust=False
        else:raise ValueError(f"Unsupported label: {label}")
        budget=f"d{args.draws}_t{args.tune}_c{args.chains}_a{args.target_accept}_dense{int(args.dense_mass)}"
        refined=label+"_refined_"+budget
        print(f"Refining {label}",flush=True)
        r.fit_model(train,name,refined,args,provider_adjust)
        archive=r.OUT/"sampling_refinements"/f"{label}_{time.time_ns()}"
        archive.mkdir(parents=True)
        for suffix in [".nc","_summary.csv","_diagnostics.json"]:
            original=r.OUT/"posteriors"/(label+suffix)
            if original.exists():shutil.copy2(original,archive/original.name)
            shutil.copy2(r.OUT/"posteriors"/(refined+suffix),original)
        diag=r.OUT/"posteriors"/f"{label}_diagnostics.json"
        info=json.loads(diag.read_text());info["label"]=label;diag.write_text(json.dumps(info,indent=2))
        score=r.OUT/f"{label}_scores.csv"
        if score.exists():shutil.move(str(score),str(archive/score.name))
        if match:
            r.cv(d,scenario,[name],args,k=k,secondary=split=="within",provider_adjust=provider_adjust)
    r.summarize()


if __name__=="__main__":main()
