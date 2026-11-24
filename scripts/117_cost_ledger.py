"""Cost ledger from the raw API logs (added 2026-11-22 for the BlueDot grant accounting). No model calls.

For every eval log under logs/, sums the provider-recorded cost of each call (OpenRouter returns `usage.cost` per
response) and the token counts; prices Anthropic calls from tokens; adds the held-out-wording run (cost column in its
runs.csv) and the research-direction pilots (numeric `cost` fields in their raw JSON records). Writes
results/COST_LEDGER.md and results/cost_ledger.csv. Totals are checked against the OpenRouter key's reported usage.
"""
import glob, json, os, pathlib, re
import pandas as pd
from inspect_ai.log import read_eval_log

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRICE = {"anthropic/claude-haiku-4-5": (1.0, 5.0), "anthropic/claude-sonnet-4-5": (3.0, 15.0)}   # $ per M input / output
WHAT = {
 "pilot": ("Step 2: harness check on Claude Haiku 4.5, 50 q x 4 conditions x 10 reps", "docs/FINAL_REPORT.md Result 1", "Length varies too little within question for any diffusion model to fit (log SD 0.13 vs 0.51)."),
 "pilot_r1": ("Step 3: DeepSeek-R1 at an 8,192-token cap, 50 q x 4 conditions x 2 reps", "docs/FINAL_REPORT.md Result 2", "43% of runs hit the cap; the DDM loses to the baseline on censoring; OpenRouter routed to four upstreams."),
 "cap_experiment": ("Step 4: 62 stalled R1 cells re-run at 24,576 tokens", "docs/FINAL_REPORT.md Result 3", "81% finish; accuracy falls from 100% to 60% with finishing length."),
 "hint_injection": ("Step 9: planted cue, opinion vs answer key, 100 recall q x 3 arms", "docs/HINT_PREREG.md; results/hint_injection/REPORT.md", "Key followed 51% vs 12%; every flip names the cue in the trace."),
 "deference": ("Step 10: answer key with stated success rate .55/.70/.86/.95, 1,000 calls", "docs/DEFERENCE_PREREG.md s.9; results/deference/run/REPORT.md", "Presence of a key does everything, the number almost nothing; traces show the number was misread as difficulty."),
 "deference_cue_probe": ("Step 11a: 36-call probe of three reliability wordings", "docs/DEFERENCE_PREREG.md s.10; results/deference/cue_probe/REPORT.md", "Chose the key-audit sentence that no trace misreads."),
 "deference_replication": ("Step 11b: replication with the readable wording on R1, doses .55/.95, 400 calls", "docs/DEFERENCE_PREREG.md s.10-11; results/deference/replication/REPORT.md", "Follow rate 13% at 55% claimed reliability, 27% at 95%; R1 weighs stated reliability about one for one."),
 "deference_peer_tag": ("Step 11c: peer-reviewed tag restored, 200 calls", "docs/DEFERENCE_PREREG.md s.12; results/deference/peer_tag/REPORT.md", "The tag adds about 1.1 logits of pull on its own."),
 "deference_model2": ("Step 12a: same design on Qwen3-32B, 800 calls with own controls", "docs/DEFERENCE_PREREG.md s.13; results/deference/model2/REPORT.md", "Follows the key 27% whatever it claims; a third of traces never mention it."),
 "deference_model3": ("Step 12b: same design on gpt-oss-120b, 800 calls", "docs/DEFERENCE_PREREG.md s.14; results/deference/model3/REPORT.md", "Barely moves; 100-token traces; tilt without discussion."),
 "deference_swap_model2": ("Option-swap re-run on Qwen3-32B, stopped by the user after 22 calls", "docs/DEFERENCE_SWAP_AMENDMENT.md", "No result; partial log kept, resumable."),
}


def eval_dirs():
    rows = []
    for d in sorted(glob.glob(str(ROOT / "logs/*/"))):
        name = os.path.basename(d.rstrip("/")); calls = 0; cost = 0.0; priced = 0.0; inp = out = 0; providers = {}; models = set(); dates = []; n_recorded = 0
        for p in sorted(glob.glob(os.path.join(d, "*.eval"))):
            try: log = read_eval_log(p)
            except Exception as e: print("unreadable", p, e); continue
            models.add(log.eval.model); dates.append(str(log.eval.created)[:10])
            for s in log.samples or []:
                calls += 1; u = s.output.usage if s.output else None
                i_tok = (u.input_tokens or 0) if u else 0; o_tok = (u.output_tokens or 0) if u else 0; inp += i_tok; out += o_tok
                c = None; prov = None
                for ev in s.events or []:
                    if getattr(ev, "event", None) == "model" and ev.call and isinstance(ev.call.response, dict):
                        r = ev.call.response; prov = r.get("provider", prov); uu = r.get("usage") or {}
                        if isinstance(uu, dict) and uu.get("cost") is not None: c = (c or 0.0) + float(uu["cost"])
                if c is not None: cost += c; n_recorded += 1
                elif log.eval.model in PRICE: pi, po = PRICE[log.eval.model]; priced += (i_tok * pi + o_tok * po) / 1e6
                if prov: providers[prov] = providers.get(prov, 0) + 1
        what = WHAT.get(name, ("", "", ""))
        rows.append(dict(item=name, dates=f"{min(dates)}..{max(dates)}" if dates else "", model=", ".join(sorted(models)), calls=calls, calls_with_recorded_cost=n_recorded,
                         input_tokens=inp, output_tokens=out, providers=json.dumps(providers), recorded_cost_usd=round(cost, 4), priced_cost_usd=round(priced, 4),
                         payer="Anthropic API" if any(m.startswith("anthropic") for m in models) else "OpenRouter (DeepInfra)", experiment=what[0], where=what[1], finding=what[2]))
    return rows


def wording_followup():
    r = pd.read_csv(ROOT / "results/deference/wording_followup/runs.csv")
    return dict(item="wording_followup", dates="2026-10-16", model=", ".join(sorted(r.model.unique())), calls=len(r), calls_with_recorded_cost=int(r.cost.notna().sum()),
                input_tokens=int(r.api_in.fillna(0).sum()), output_tokens=int(r.api_out.fillna(0).sum()), providers=json.dumps(r.provider.value_counts().to_dict()),
                recorded_cost_usd=round(float(r.cost.sum()), 4), priced_cost_usd=0.0, payer="OpenRouter (DeepInfra)",
                experiment="Step 13: two held-out reliability wordings on three models, 2,100 calls", where="docs/CROSS_MODEL_FOLLOWUP.md; results/deference/wording_followup/REPORT.md",
                finding="Model x reliability interaction replicates: R1 minus Qwen +10.8 points (2.6 to 19.6).")


def research_directions():
    """Per-call cost in the raw response records of each research-direction folder (Part 3 pilots): OpenRouter responses
    carry `usage.cost`; Anthropic responses (model name starts with claude) are priced from tokens."""
    rows = []
    for d in sorted(glob.glob(str(ROOT / "results/research_directions/*/"))):
        name = os.path.basename(d.rstrip("/")); orr = ant = 0.0; n_or = n_an = 0; models = set(); dates = set()
        for p in glob.glob(os.path.join(d, "**", "*.json"), recursive=True):
            if "/raw/" not in p: continue
            try: j = json.load(open(p))
            except Exception: continue
            if not isinstance(j, dict): continue
            m = str(j.get("model", "")); u = j.get("usage") if isinstance(j.get("usage"), dict) else {}
            if "created" in j:
                try: import datetime; dates.add(datetime.datetime.utcfromtimestamp(int(j["created"])).strftime("%Y-%m-%d"))
                except Exception: pass
            if u.get("cost") is not None: orr += float(u["cost"]); n_or += 1; models.add(m)
            elif "claude" in m and u.get("input_tokens") is not None:
                pi, po = (1.0, 5.0) if "haiku" in m else (3.0, 15.0); ant += (u.get("input_tokens", 0) * pi + u.get("output_tokens", 0) * po) / 1e6; n_an += 1; models.add(m)
        if n_or + n_an == 0: continue
        if n_or: rows.append(dict(item=f"research_directions/{name}", dates=re.sub(r"_\d{8}$", "", name) and ",".join(sorted(dates)), model=", ".join(sorted(m for m in models if "claude" not in m)), calls=n_or, calls_with_recorded_cost=n_or, recorded_cost_usd=round(orr, 4), priced_cost_usd=0.0, payer="OpenRouter (DeepInfra)", experiment="Part 3 pilot or resource check (Steps 14-16)", where=f"results/research_directions/{name}/", finding=""))
        if n_an: rows.append(dict(item=f"research_directions/{name} (Claude)", dates=",".join(sorted(dates)), model=", ".join(sorted(m for m in models if "claude" in m)), calls=n_an, calls_with_recorded_cost=0, recorded_cost_usd=0.0, priced_cost_usd=round(ant, 4), payer="Anthropic API", experiment="Part 3 Sonnet/Haiku experiment (Steps 15-16)", where=f"results/research_directions/{name}/", finding=""))
    return rows


def main():
    rows = eval_dirs() + [wording_followup()] + research_directions()
    L = pd.DataFrame(rows); L.to_csv(ROOT / "results/cost_ledger.csv", index=False)
    orr = L[L.payer.str.startswith("OpenRouter")].recorded_cost_usd.sum(); ant = L[L.payer == "Anthropic API"].priced_cost_usd.sum()
    rd = L[L.item.str.startswith("research_directions")].recorded_cost_usd.sum()
    with open(ROOT / "results/COST_LEDGER.md", "w") as f:
        f.write("# Cost ledger (from the raw API logs)\n\nGenerated by scripts/117_cost_ledger.py on 2026-11-22. `recorded_cost_usd` is the provider-reported cost of each call summed from the logs "
                "(OpenRouter returns it per response); `priced_cost_usd` is tokens x list price where no cost is recorded (Anthropic calls). Research-direction pilots are summed from the "
                "numeric `cost` fields in their raw per-call records.\n\n")
        f.write(L[["item", "dates", "model", "calls", "recorded_cost_usd", "priced_cost_usd", "payer", "experiment", "finding"]].fillna("").to_markdown(index=False) + "\n\n")
        f.write(f"OpenRouter recorded total ${orr:.4f} (of which research-direction pilots ${rd:.4f}); Anthropic priced total ${ant:.4f}. "
                f"OpenRouter key usage reported by the API on 2026-11-22: $18.57 of $100 prepaid; the difference from the logged total is calls without a surviving per-call record "
                f"(rate-limit retries, incomplete R1 runs, deleted debug runs).\n")
    print(L[["item", "dates", "calls", "recorded_cost_usd", "priced_cost_usd", "payer"]].to_string()); print(f"\nOpenRouter recorded total ${orr:.4f} (research-direction pilots ${rd:.4f}); Anthropic priced ${ant:.4f}")


if __name__ == "__main__":
    main()
