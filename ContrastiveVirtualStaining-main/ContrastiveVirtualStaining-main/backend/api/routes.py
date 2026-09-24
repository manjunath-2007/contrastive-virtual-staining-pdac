from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import os, json, glob

from services.ml_service import (
    read_config, read_path_csv, demo_feats_dir, results_root,
    latest_run_dir, parse_run_metrics, get_fold_roc_images, ml_root,
    start_experiment, get_status, path_csv,
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/project")
def project_info():
    return {
        "title": "Contrastive Virtual Staining Enhances Deep Learning-Based PDAC Subtyping from H&E-Stained Tissue Cores",
        "problem": "PDAC subtyping from H&E tissue cores is challenging. Subtype-related information may require additional staining (e.g. KRT81, HNF1A).",
        "solution": "AI-based virtual staining combined with DSMIL (Deep-learning based Multiple Instance Learning) to support PDAC subtype classification.",
        "dataset_note": "Current dataset: Synthetic Demo Dataset — for pipeline validation only.",
        "disclaimer": "Research prototype — not for clinical diagnosis.",
    }


@router.get("/config")
def get_config():
    cfg = read_config()
    return cfg


@router.get("/dataset")
def dataset_info():
    df = read_path_csv()
    feats_dir = demo_feats_dir()
    feat_files = list(feats_dir.glob("*.pt")) if feats_dir.exists() else []

    class0 = int((df["label"] == 0).sum())
    class1 = int((df["label"] == 1).sum())

    # Try to read feature dimension from first file
    feat_dim = None
    try:
        import torch
        if feat_files:
            t = torch.load(str(feat_files[0]), weights_only=True)
            feat_dim = int(t.shape[-1])
    except Exception:
        feat_dim = 512  # fallback from config

    return {
        "path_csv_exists": path_csv().exists(),
        "total_samples": len(df),
        "class_0_count": class0,
        "class_1_count": class1,
        "feature_files_count": len(feat_files),
        "feature_dim": feat_dim,
        "demo_feats_exists": feats_dir.exists(),
        "dataset_type": "Synthetic Demo Dataset",
        "note": "Demo Dataset — Synthetic Data. Not real clinical data.",
    }


@router.get("/patients")
def get_patients():
    df = read_path_csv()
    rows = []
    for _, row in df.iterrows():
        p = Path(str(row["path"]))
        rows.append({
            "file": p.name,
            "label": int(row["label"]),
            "path": str(row["path"]),
            "exists": p.exists(),
        })
    return {"patients": rows}


@router.get("/results")
def list_results():
    base = results_root()
    pattern = str(base / "**" / "config.yaml")
    configs = glob.glob(pattern, recursive=True)
    runs = []
    for c in sorted(configs, key=os.path.getmtime, reverse=True):
        run_dir = Path(c).parent
        roc_exists = (run_dir / "ROC.png").exists()
        metrics = parse_run_metrics(run_dir)
        runs.append({
            "run_dir": str(run_dir),
            "name": run_dir.name,
            "timestamp": run_dir.stat().st_mtime,
            "roc_exists": roc_exists,
            "metrics": metrics,
        })
    return {"runs": runs}


@router.get("/results/latest")
def latest_result():
    run_dir = latest_run_dir()
    if not run_dir:
        raise HTTPException(404, "No results found.")
    metrics = parse_run_metrics(run_dir)
    fold_rocs = get_fold_roc_images(run_dir)
    return {
        "run_dir": str(run_dir),
        "name": run_dir.name,
        "roc_exists": (run_dir / "ROC.png").exists(),
        "metrics": metrics,
        "fold_count": len(fold_rocs),
        "timestamp": run_dir.stat().st_mtime,
    }


@router.get("/results/roc")
def get_roc_image():
    run_dir = latest_run_dir()
    if not run_dir:
        raise HTTPException(404, "No results found.")
    roc_path = run_dir / "ROC.png"
    if not roc_path.exists():
        raise HTTPException(404, "ROC.png not found.")
    return FileResponse(str(roc_path), media_type="image/png")


@router.get("/results/roc/fold/{fold_idx}")
def get_fold_roc(fold_idx: int):
    run_dir = latest_run_dir()
    if not run_dir:
        raise HTTPException(404, "No results found.")
    roc_path = run_dir / f"Fold_{fold_idx}" / "ROC.png"
    if not roc_path.exists():
        raise HTTPException(404, f"ROC.png for Fold {fold_idx} not found.")
    return FileResponse(str(roc_path), media_type="image/png")


@router.get("/run/status")
def run_status():
    return get_status()


@router.post("/run")
def run_experiment(body: dict = {}):
    mode = body.get("mode", "demo")
    result = start_experiment(mode)
    if not result["ok"]:
        raise HTTPException(409, result["error"])
    return {"message": "Experiment started.", "mode": mode}
