import os, sys, subprocess, threading, time, glob, json
from datetime import datetime
from pathlib import Path

import yaml
import pandas as pd

ML_ROOT = Path(__file__).parent.parent.parent  # ContrastiveVirtualStaining-main/ parent of backend/

# ── experiment state ──────────────────────────────────────────────────────────
_state = {
    "status": "IDLE",          # IDLE | RUNNING | COMPLETED | FAILED
    "mode": "demo",            # demo | real
    "start_time": None,
    "end_time": None,
    "log": [],
    "process": None,
}
_lock = threading.Lock()


# ── helpers ───────────────────────────────────────────────────────────────────

def ml_root() -> Path:
    return ML_ROOT


def config_path() -> Path:
    return ML_ROOT / "config.yaml"


def path_csv() -> Path:
    return ML_ROOT / "Path.csv"


def demo_feats_dir() -> Path:
    return ML_ROOT / "demo_feats"


def results_root() -> Path:
    return ML_ROOT / "results"


def read_config() -> dict:
    with open(config_path()) as f:
        return yaml.safe_load(f)


def read_path_csv() -> pd.DataFrame:
    df = pd.read_csv(path_csv(), header=None, names=["path", "label"])
    return df


# ── results detection ─────────────────────────────────────────────────────────

def _all_run_dirs(mode: str = "demo") -> list[Path]:
    """Return all run dirs sorted newest-first."""
    base = results_root()
    pattern = str(base / "**" / "config.yaml")
    configs = glob.glob(pattern, recursive=True)
    dirs = [Path(c).parent for c in configs]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs


def latest_run_dir(mode: str = "demo") -> Path | None:
    dirs = _all_run_dirs(mode)
    return dirs[0] if dirs else None


def parse_run_metrics(run_dir: Path) -> dict:
    """Extract metrics from a saved metrics.json or, as a fallback, from the
    TensorBoard event files produced by the training pipeline."""
    metrics_file = run_dir / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            return json.load(f)

    metrics = {}
    try:
        from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
        auc_values = []
        for fd in sorted(run_dir.glob("Fold_*")):
            evt = list((fd / "TBRuns").glob("events.out.tfevents.*"))
            if not evt:
                continue
            ea = EventAccumulator(str(evt[0]))
            ea.Reload()
            for tag in ea.Tags()["scalars"]:
                if "auc" in tag.lower():
                    vals = ea.Scalars(tag)
                    if vals:
                        auc_values.append(vals[-1].value)
        if auc_values:
            metrics["auc"] = sum(auc_values) / len(auc_values)
    except Exception:
        pass
    return metrics


def get_fold_roc_images(run_dir: Path) -> list[str]:
    images = []
    for i in range(10):
        p = run_dir / f"Fold_{i}" / "ROC.png"
        if p.exists():
            images.append(str(p))
    return images


# ── experiment runner ─────────────────────────────────────────────────────────

def _stream_process(proc):
    for line in iter(proc.stdout.readline, ""):
        with _lock:
            _state["log"].append(line.rstrip())
    proc.stdout.close()
    proc.wait()
    with _lock:
        _state["end_time"] = datetime.now().isoformat()
        if proc.returncode == 0:
            _state["status"] = "COMPLETED"
        else:
            _state["status"] = "FAILED"
        _state["process"] = None


def start_experiment(mode: str = "demo") -> dict:
    with _lock:
        if _state["status"] == "RUNNING":
            return {"ok": False, "error": "Experiment already running."}
        _state["status"] = "RUNNING"
        _state["mode"] = mode
        _state["start_time"] = datetime.now().isoformat()
        _state["end_time"] = None
        _state["log"] = []

    run_script = str(ML_ROOT / "RUN_PROJECT.py")
    python = sys.executable
    env = os.environ.copy()
    env["EXPERIMENT_LOCATION"] = str(results_root())

    proc = subprocess.Popen(
        [python, run_script],
        cwd=str(ML_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    with _lock:
        _state["process"] = proc

    t = threading.Thread(target=_stream_process, args=(proc,), daemon=True)
    t.start()
    return {"ok": True}


def get_status() -> dict:
    with _lock:
        log_copy = list(_state["log"])
        return {
            "status": _state["status"],
            "mode": _state["mode"],
            "start_time": _state["start_time"],
            "end_time": _state["end_time"],
            "log": log_copy,
        }
