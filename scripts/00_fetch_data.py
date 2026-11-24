"""Fetch raw datasets at the same revisions inspect_evals pins.

usage: python scripts/00_fetch_data.py --dataset wmdp
       python scripts/00_fetch_data.py --dataset cybermetric --size 2000
"""
import argparse, json, pathlib, urllib.request

WMDP_REV = "7125571f22f032c56415e7980f48d877dd830ff8"
CYBERMETRIC_REV = "205262cdf5022ba890e792efd176fb19d42913fa"
RAW = pathlib.Path("data/raw")


def fetch_wmdp():
    from datasets import load_dataset  # needs HF access
    ds = load_dataset("cais/wmdp", "wmdp-cyber", split="test", revision=WMDP_REV)
    out = RAW / "wmdp_cyber.jsonl"
    with out.open("w") as f:
        for i, r in enumerate(ds):
            f.write(json.dumps({"qid": f"wmdp-{i:04d}", "question": r["question"],
                                "choices": r["choices"], "answer_idx": r["answer"]}) + "\n")
    print(f"wrote {len(ds)} rows -> {out}")


def fetch_cybermetric(size: int):
    url = f"https://raw.githubusercontent.com/cybermetric/CyberMetric/{CYBERMETRIC_REV}/CyberMetric-{size}-v1.json"
    raw = json.load(urllib.request.urlopen(url))
    out = RAW / f"cybermetric_{size}.jsonl"
    with out.open("w") as f:
        for i, q in enumerate(raw["questions"]):
            letters = sorted(q["answers"])
            f.write(json.dumps({"qid": f"cm{size}-{i:05d}", "question": q["question"],
                                "choices": [q["answers"][k] for k in letters],
                                "answer_idx": letters.index(q["solution"])}) + "\n")
    print(f"wrote {len(raw['questions'])} rows -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["wmdp", "cybermetric"], required=True)
    ap.add_argument("--size", type=int, default=2000)
    a = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    fetch_wmdp() if a.dataset == "wmdp" else fetch_cybermetric(a.size)
