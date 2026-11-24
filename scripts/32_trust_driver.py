"""Run sequential budget-checked batches for the already frozen trust study.

No prompt/model/statistical changes. No automatic credit purchase or effect analysis.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("trust_collection", ROOT / "scripts/31_trust_collect.py")
collect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect)


def run(max_batches):
    collect.require_no_batch()
    for number in range(1, max_batches + 1):
        status = collect.status()
        if status["complete"]:
            print("Collection complete. Running the predeclared analysis.", flush=True)
            subprocess.run([sys.executable, str(ROOT / "scripts/33_trust_analysis.py")], check=True)
            return
        collect.preflight_config()
        pointer = collect.OUT / "live_preflight_location.json"
        state = json.loads(pointer.read_text())
        fetched = subprocess.run(["curl", "--parallel", "--parallel-max", "5", "--config", state["config"]])
        if fetched.returncode:
            # preflight cleans private files even on malformed/incomplete fetches.
            try:
                collect.preflight()
            finally:
                raise RuntimeError("Read-only preflight fetch failed; no model batch launched")
        collect.preflight()
        collect.prepare(100)
        batch = collect.active_batch()
        if batch is None:
            status = collect.status()
            if status["exhausted_ids"]:
                raise RuntimeError("Operational retry limit exhausted; collection remains incomplete")
            if status["cooling_ids"]:
                print("Rate-limited trials cooling; recheck in 60 seconds.", flush=True)
                time.sleep(60)
                continue
            if not status["complete"]:
                raise RuntimeError("No runnable requests; collection incomplete")
            subprocess.run([sys.executable, str(ROOT / "scripts/33_trust_analysis.py")], check=True)
            return
        print(f"Starting batch {number}; {len(batch['trials'])} requests.", flush=True)
        try:
            process = subprocess.Popen(["curl", "--parallel", "--parallel-max", "6", "--config", batch["config"]])
            while True:
                try:
                    code = process.wait(timeout=45)
                    break
                except subprocess.TimeoutExpired:
                    print(f"Batch {number} still running; no treatment effects inspected.", flush=True)
        except BaseException:
            if 'process' in locals() and process.poll() is None:
                process.terminate()
                process.wait()
            raise
        finally:
            # Only executes after the child curl process exits or is terminated.
            collect.finish_batch()
        print(f"Batch {number} exited {code}; live preflight will refresh before continuing.", flush=True)
    status = collect.status()
    if status["complete"]:
        subprocess.run([sys.executable, str(ROOT / "scripts/33_trust_analysis.py")], check=True)
    else:
        raise RuntimeError("Reached driver batch limit. Collection incomplete; resume the same frozen manifest.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-batches", type=int, default=300)
    args = parser.parse_args()
    if not 1 <= args.max_batches <= 1000:
        parser.error("max-batches must be 1..1000")
    state = dict(pid=os.getpid(), started_at=datetime.now(timezone.utc).isoformat(),
                 status="running", driver_sha256=collect.sha(Path(__file__)),
                 analysis_sha256=collect.sha(ROOT / "scripts/33_trust_analysis.py"))
    collect.write_json(collect.OUT / "driver_state.json", state)
    try:
        run(args.max_batches)
    except BaseException as exc:
        state.update(status="stopped_incomplete", stopped_at=datetime.now(timezone.utc).isoformat(), error=str(exc))
        collect.write_json(collect.OUT / "driver_state.json", state)
        raise
    else:
        state.update(status="complete", finished_at=datetime.now(timezone.utc).isoformat())
        collect.write_json(collect.OUT / "driver_state.json", state)
