"""Resumable delivery for the frozen trust experiment; no automatic API spending.

preflight-config and prepare print explicit curl commands. Execute them separately.
No treatment-effect analysis is exposed here. See TRUST_COLLECTION_OPERATIONS.md.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import tempfile
import time

from outcomes import parse_answer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/deference/trust_planning"
OPS = ROOT / "docs/TRUST_COLLECTION_OPERATIONS.md"
MODELS = {"R1": "deepseek/deepseek-r1-0528", "Qwen3": "qwen/qwen3-32b", "gpt-oss": "openai/gpt-oss-120b"}
RESERVE = 5.
REFUSAL = re.compile(r"(?i)(I can'?t|I cannot|I won'?t|not able to) (help|assist|provide)")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def manifest():
    m = json.loads((OUT / "manifest.json").read_text())
    planning = json.loads((OUT / "planning.json").read_text())
    checks = [(OUT / "planning.json", m["planning_sha256"]),
              (ROOT / "docs/TRUST_FOLLOWUP.md", m["protocol_sha256"]),
              (ROOT / "scripts/30_trust_design.py", planning["script_sha256"]),
              (ROOT / "data/processed/two_choice.jsonl", m["question_source_sha256"]),
              (ROOT / "data/processed/task_type.csv", m["task_labels_sha256"])]
    for path, expected in checks:
        if sha(path) != expected:
            raise ValueError(f"Frozen artifact changed: {path.name}")
    if len(m["trials"]) != 30 * m["n_questions"] or len({t["sample_id"] for t in m["trials"]}) != len(m["trials"]):
        raise ValueError("Invalid trial coverage")
    return m


def active_batch():
    path = OUT / "active_batch.json"
    return json.loads(path.read_text()) if path.exists() else None


def require_no_batch():
    if active_batch() is not None:
        raise ValueError("A prepared/running batch exists. Wait for curl to exit, then finish-batch.")


def cap_cost(trial, endpoint):
    request = trial["request"]
    size = 4 * (len(json.dumps(request["messages"], ensure_ascii=False).encode()) + 1024)
    p = endpoint["pricing"]
    return size * float(p["prompt"]) + request["max_tokens"] * float(p["completion"])


def index_attempts():
    result = defaultdict(list)
    for path in (OUT / "raw").glob("*.attempt*.json"):
        result[path.name.rsplit(".attempt", 1)[0]].append(path)
    return result


def delivered(trial, paths):
    valid = []
    for path in paths:
        try:
            x = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        choices = x.get("choices") or []
        if x.get("error") or not choices or choices[0].get("error"):
            continue
        if x.get("provider") != "DeepInfra" or x.get("model") != trial["request"]["model"]:
            raise ValueError(f"Unexpected model/provider in {path.name}")
        if len(choices) != 1 or not isinstance(choices[0].get("message"), dict):
            continue
        if (x.get("usage") or {}).get("completion_tokens") is None:
            continue
        valid.append((path, x))
    if len(valid) > 1:
        raise ValueError(f"Duplicate valid responses for {trial['sample_id']}")
    return valid[0] if valid else (None, None)


def api_key():
    from dotenv import dotenv_values
    value = dotenv_values(ROOT / ".env").get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not value:
        raise ValueError("OPENROUTER_API_KEY is not configured")
    return value


def preflight_config():
    require_no_batch()
    manifest()
    pointer = OUT / "live_preflight_location.json"
    if pointer.exists():
        raise ValueError("A private preflight configuration already exists; complete preflight first")
    folder = Path(tempfile.mkdtemp(prefix="ddm-trust-preflight-", dir="/private/tmp"))
    config = folder / "requests.curl"
    key = api_key()
    sources = {"credits": "https://openrouter.ai/api/v1/credits", "allowance": "https://openrouter.ai/api/v1/auth/key"}
    sources.update({model: f"https://openrouter.ai/api/v1/models/{endpoint}/endpoints" for model, endpoint in MODELS.items()})
    fd = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        for i, (name, url) in enumerate(sources.items()):
            if i:
                f.write("next\n")
            f.write("url = " + json.dumps(url) + "\n")
            if name in ("credits", "allowance"):
                f.write("header = " + json.dumps("Authorization: Bearer " + key) + "\n")
            f.write("output = " + json.dumps(str(folder / (name + ".json"))) + "\nmax-time = 30\nsilent\nshow-error\n")
    write_json(pointer, dict(folder=str(folder), config=str(config)))
    print(f"curl --parallel --parallel-max 5 --config {shlex.quote(str(config))}")


def preflight():
    require_no_batch()
    m = manifest()
    pointer = OUT / "live_preflight_location.json"
    state = json.loads(pointer.read_text())
    folder = Path(state["folder"])
    endpoints = {}
    try:
        attempts = index_attempts()
        pending = [t for t in m["trials"] if delivered(t, attempts[t["sample_id"]])[1] is None]
        for model in MODELS:
            data = json.loads((folder / (model + ".json")).read_text())["data"]
            candidates = [e for e in data["endpoints"] if e.get("provider_name") == "DeepInfra"]
            if len(candidates) != 1 or candidates[0].get("status") != 0:
                raise ValueError(f"Pinned endpoint unavailable: {model}")
            endpoint = candidates[0]
            for trial in pending:
                if trial["model"] != model:
                    continue
                request = trial["request"]
                input_bound = 4 * (len(json.dumps(request["messages"], ensure_ascii=False).encode()) + 1024)
                if endpoint.get("max_completion_tokens", 0) < request["max_tokens"] or endpoint.get("context_length", 0) < input_bound + request["max_tokens"]:
                    raise ValueError(f"Endpoint capacity cannot cover conservative token envelope: {model}")
            endpoints[model] = endpoint
        credits = json.loads((folder / "credits.json").read_text())["data"]
        allowance = json.loads((folder / "allowance.json").read_text())["data"]
        balance = credits["total_credits"] - credits["total_usage"]
        remaining = allowance.get("limit_remaining")
        bound = sum(cap_cost(t, endpoints[t["model"]]) for t in pending)
        needed = bound + (RESERVE if pending else 0)
        value = dict(checked_at=datetime.now(timezone.utc).isoformat(),
                     manifest_sha256=sha(OUT / "manifest.json"), operations_sha256=sha(OPS),
                     runner_sha256=sha(Path(__file__)), endpoint_by_model=endpoints,
                     account_balance_remaining=balance, key_allowance_remaining=remaining,
                     planned_calls=len(m["trials"]), remaining_calls=len(pending),
                     full_success_cap_cost_bound=bound, retry_reserve=RESERVE,
                     required_remaining_credit=needed,
                     passed=balance >= needed and (remaining is None or remaining >= needed),
                     input_bound_method="4*(serialized message UTF-8 bytes+1024); conservative, not exact tokenization")
        history = OUT / "preflight_history"
        history.mkdir(exist_ok=True)
        if (OUT / "live_preflight.json").exists():
            write_json(history / (sha(OUT / "live_preflight.json") + ".json"), json.loads((OUT / "live_preflight.json").read_text()))
        write_json(OUT / "live_preflight.json", value)
        print(f"Balance ${balance:.2f}; required ${needed:.2f} including ${RESERVE:.2f} retry reserve; budget {'PASS' if value['passed'] else 'FAIL'}.")
    finally:
        for p in folder.iterdir():
            p.unlink()
        folder.rmdir()
        pointer.unlink()


def validate_budget(m, budget):
    if not budget.get("passed"):
        raise ValueError("Insufficient full-study credit/allowance; no model requests prepared")
    checks = [("manifest_sha256", OUT / "manifest.json"), ("operations_sha256", OPS), ("runner_sha256", Path(__file__))]
    for key, path in checks:
        if budget[key] != sha(path):
            raise ValueError("Preflight integrity check failed; refresh preflight")
    age = time.time() - datetime.fromisoformat(budget["checked_at"]).timestamp()
    if age < 0 or age > 900 or budget["planned_calls"] != len(m["trials"]):
        raise ValueError("Stale/mismatched preflight; refresh before preparing another batch")


def retry_state(paths):
    ordinary, limited, due = 0, 0, 0.
    from email.utils import parsedate_to_datetime
    for path in paths:
        try:
            x = json.loads(path.read_text())
            is_limit = (x.get("error") or {}).get("code") == 429 and not x.get("usage") and not x.get("choices")
        except (OSError, json.JSONDecodeError):
            is_limit = False
        if not is_limit:
            ordinary += 1
            continue
        limited += 1
        stamp = path.stat().st_mtime
        after = path.with_suffix(".retry_after")
        delay_due = stamp + 900
        if after.exists() and after.read_text().strip():
            text = after.read_text().strip()
            try:
                delay = float(text)
                if not 0 <= delay < float("inf"):
                    raise ValueError("Invalid delay")
                delay_due = max(delay_due, stamp + delay)
            except ValueError:
                try:
                    delay_due = max(delay_due, parsedate_to_datetime(text).timestamp())
                except (ValueError, TypeError, OverflowError):
                    pass
        due = max(due, delay_due)
    return ordinary, limited, due


def prepare(batch_size):
    require_no_batch()
    m = manifest()
    budget = json.loads((OUT / "live_preflight.json").read_text())
    validate_budget(m, budget)
    attempts = index_attempts()
    pending, exhausted, cooling = [], [], []
    for trial in m["trials"]:
        paths = attempts[trial["sample_id"]]
        if delivered(trial, paths)[1] is not None:
            continue
        ordinary, limited, due = retry_state(paths)
        if ordinary >= 3 or limited >= 6:
            exhausted.append(trial["sample_id"])
        elif due > time.time():
            cooling.append(trial["sample_id"])
        elif len(pending) < batch_size:
            attempt = 1 + max([int(p.stem.rsplit("attempt", 1)[1]) for p in paths], default=0)
            pending.append((trial, attempt))
    if not pending:
        print(f"No ready requests; exhausted={len(exhausted)}, cooling={len(cooling)}. Collection may be incomplete.")
        return
    bound = sum(cap_cost(t, budget["endpoint_by_model"][t["model"]]) for t, _ in pending)
    if bound + RESERVE > min(budget["account_balance_remaining"], budget["key_allowance_remaining"] if budget["key_allowance_remaining"] is not None else float("inf")):
        raise ValueError("Batch plus reserve exceeds available credit")
    requests, raw, batches = [OUT / x for x in ("requests", "raw", "batches")]
    for path in (requests, raw, batches):
        path.mkdir(exist_ok=True)
    key = api_key()
    fd, name = tempfile.mkstemp(prefix="ddm-trust-", suffix=".curl", dir="/private/tmp")
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as f:
        for i, (trial, attempt) in enumerate(pending):
            request_path = requests / (trial["sample_id"] + ".json")
            if request_path.exists() and json.loads(request_path.read_text()) != trial["request"]:
                raise ValueError("Changed request file; audit before collection")
            write_json(request_path, trial["request"])
            output = raw / f"{trial['sample_id']}.attempt{attempt}.json"
            if output.exists():
                raise ValueError("Refusing to overwrite a raw attempt")
            if i:
                f.write("next\n")
            options = dict(url="https://openrouter.ai/api/v1/chat/completions",
                           header=["Authorization: Bearer " + key, "Content-Type: application/json", "Connection: close"],
                           data_binary="@" + str(request_path), output=str(output), max_time="600", connect_timeout="20",
                           write_out="%output{" + str(output.with_suffix('.retry_after')) + "}%header{retry-after}")
            for opt, value in options.items():
                for v in value if isinstance(value, list) else [value]:
                    f.write(opt.replace("_", "-") + " = " + json.dumps(v) + "\n")
            f.write("silent\nshow-error\nhttp1.1\n")
    batch = dict(config=name, prepared_at=datetime.now(timezone.utc).isoformat(),
                 manifest_sha256=sha(OUT / "manifest.json"), preflight_sha256=sha(OUT / "live_preflight.json"),
                 maximum_cost=bound, exhausted=exhausted, cooling=cooling,
                 trials=[dict(sample_id=t["sample_id"], attempt=n) for t, n in pending])
    write_json(batches / (Path(name).stem + ".json"), batch)
    write_json(OUT / "active_batch.json", batch)
    print(f"Prepared {len(pending)} requests; batch cap-cost ${bound:.2f}.")
    print(f"curl --parallel --parallel-max 6 --config {shlex.quote(name)}")
    print("After curl exits, run --stage finish-batch to remove its private configuration.")


def finish_batch():
    batch = active_batch()
    if batch is None:
        raise ValueError("No active batch")
    # This explicit operator stage must only be invoked after curl has exited.
    config = Path(batch["config"])
    if config.exists():
        config.unlink()
    write_json(OUT / "batches" / (config.stem + ".finished.json"), dict(finished_at=datetime.now(timezone.utc).isoformat()))
    (OUT / "active_batch.json").unlink()
    status()


def status():
    m = manifest()
    attempts = index_attempts()
    outcomes, completed, missing, exhausted, cooling, cost = Counter(), [], [], [], [], 0.
    for trial in m["trials"]:
        paths = attempts[trial["sample_id"]]
        path, x = delivered(trial, paths)
        if x is None:
            missing.append(trial["sample_id"])
            ordinary, limited, due = retry_state(paths)
            if ordinary >= 3 or limited >= 6:
                exhausted.append(trial["sample_id"])
            elif due > time.time():
                cooling.append(trial["sample_id"])
            continue
        completed.append(trial["sample_id"])
        text = x["choices"][0]["message"].get("content") or ""
        if not isinstance(text, str):
            raise ValueError("Unexpected completion content")
        if REFUSAL.search(text.replace("’", "'")):
            outcome = "refusal"
        elif parse_answer(text) is not None:
            outcome = "answered"
        elif x["choices"][0].get("finish_reason") == "length":
            outcome = "censored"
        else:
            outcome = "unparseable" if text.strip() else "incomplete"
        outcomes[outcome] += 1
        cost += float(x["usage"].get("cost") or 0)
    value = dict(updated_at=datetime.now(timezone.utc).isoformat(), complete=not missing,
                 planned=len(m["trials"]), completed=len(completed), missing_ids=missing,
                 outcomes=dict(outcomes), exhausted_ids=exhausted, cooling_ids=cooling,
                 api_recorded_valid_response_cost=cost, manifest_sha256=sha(OUT / "manifest.json"),
                 active_batch=bool(active_batch()), effects_analyzed=False)
    write_json(OUT / "collection_status.json", value)
    preflight_path = OUT / "live_preflight.json"
    preflight = json.loads(preflight_path.read_text()) if preflight_path.exists() else {}
    (OUT / "COLLECTION.md").write_text(
        "# Correct/wrong-key experiment: collection status\n\n"
        f"Valid provider responses: **{len(completed)}/{len(m['trials'])}**.\n\n"
        f"Latest preflight passed: **{preflight.get('passed', False)}**. "
        f"Account balance at check: ${preflight.get('account_balance_remaining', 0):.2f}. "
        f"Required credit including retry reserve: ${preflight.get('required_remaining_credit', 0):.2f}.\n\n"
        "Raw responses and failed attempts are retained. No treatment-effect inference is issued by this runner. "
        "An incomplete collection must not be presented as the planned confirmatory experiment.\n\n"
        "Protocol: docs/TRUST_FOLLOWUP.md. Delivery rules: docs/TRUST_COLLECTION_OPERATIONS.md. "
        "Frozen exact requests: manifest.json. Run scripts/31_trust_collect.py --help for stages.\n")
    print(f"Delivered {len(completed)}/{len(m['trials'])}; exhausted {len(exhausted)}, cooling {len(cooling)}; no effects analyzed.")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["preflight-config", "preflight", "prepare", "finish-batch", "status"])
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        parser.error("Batch size must be between 1 and 100")
    if args.stage == "prepare":
        prepare(args.batch_size)
    else:
        globals()[args.stage.replace("-", "_")]()
