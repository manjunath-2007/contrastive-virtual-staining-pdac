# Contrastive Virtual Staining for PDAC Subtyping

**Enhancing PDAC subtyping from routine H&E with synthetic IHC**

*A research prototype for weakly-supervised Multiple Instance Learning (MIL) based pancreatic ductal adenocarcinoma (PDAC) subtype classification.*

> ⚠️ **Current dataset is SYNTHETIC DEMO DATA** — used for pipeline validation only. It is **not** real clinical data and model results are **not** clinical findings. See [Limitations](#limitations).

---

## 1. Overview

This repository implements a **Multiple Instance Learning (MIL)** pipeline for automatic subtyping of pancreatic ductal adenocarcinoma (PDAC). The framework classifies PDAC subtypes from whole-slide image (WSI) features using a **DSMIL** (Dual-Stream Multiple Instance Learning) architecture.

In this research direction, the goal is to predict immunohistochemistry (IHC)-based PDAC subtypes from routine **H&E** tissue, including potentially **synthetically stained IHC** inputs. Each patient slide is represented as a *bag* of patch-level feature embeddings, and a patient-level label (subtype) supervises the bag.

**The current repository mainly implements downstream classification/evaluation using precomputed features.** The complete virtual-staining generator is **not** included in this repository.

## 2. Problem Statement

Pancreatic ductal adenocarcinoma (PDAC) subtyping relies on IHC markers such as **KRT81** and **HNF1A**. Manual IHC evaluation is time-consuming, costly, and subject to inter-observer variability. Predicting subtype-defining markers directly from routine H&E-stained tissue cores would streamline diagnostics and reduce additional staining. The challenge is the weak (bag-level) supervision: a patient-level label must drive learning over many unlabeled patches.

## 3. Proposed Workflow

```
H&E Tissue Core  ->  Tissue Patches  ->  Precomputed Features  ->  DSMIL / MIL
                 ->  5-Fold Cross Validation
                 ->  PDAC Subtype Classification
                 ->  ROC / AUC
```

1. **Tissue Core.** Routine H&E (or IHC / synthetic-IHC) whole-slide image.
2. **Tiling.** The WSI is tiled into non-overlapping patches (e.g., 224×224 px).
3. **Feature Extraction.** Each patch is encoded into a fixed-dimensional embedding by a frozen CNN (e.g., ResNet18 or a UNI pathology foundation model).
4. **MIL.** A DSMIL network jointly trains instance- and bag-level classifiers over each patient's bag of embeddings.
5. **Evaluation.** Patient-level predictions are assessed with 5-fold stratified cross-validation and ROC/AUC.

## 4. System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          React + TypeScript                           │
│                          (frontend, :5173)                            │
│                            Vite dev server                            │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ HTTP /api  (axios -> http://localhost:8000/api)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                            FastAPI                                    │
│                          (backend, :8000)                            │
│            uvicorn backend.main:app  --reload --port 8000            │
└───────────────────────────────┬──────────────────────────────────────┘
                                │ service / orchestration
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                            ML Service                                 │
│                       backend/services/ml_service.py                 │
│   launches RUN_PROJECT.py -> train.py -> DSMIL  ->  results/         │
└──────────────────────────────────────────────────────────────────────┘
```

## 5. ML Methodology

### DSMIL — Dual-Stream Multiple Instance Learning

`dsmil.py` implements DSMIL ([Li et al., 2021](#research-paper--reference)), composed of:

- **Instance classifier (`FCLayer`)** — a linear layer producing instance (patch)-level logits.
- **Bag classifier (`BClassifier`)** — a dual-stream attention module that aggregates patch embeddings into a bag representation and produces the bag (slide)-level prediction.
- **`MILNet`** — wires the two classifiers together; returns instance logits, bag prediction, attention matrix `A`, and the aggregated representation `B`.

### Multiple Instance Learning (MIL)

Each patient slide is a *bag* of `N` patch embeddings. The bag label supervises learning without patch-level labels:

```
bag_i = { x_1, x_2, ..., x_N }   x_j ∈ R^512     y_i ∈ {0, 1}
```

The instance classifier scores each patch; the bag classifier uses attention over instances to produce the slide-level prediction.

### 5-Fold Cross Validation

Splits are generated with a **stratified** K-fold at the **patient level** (no cross-fold leakage), see `Train_Test_Splitter.py`:

```python
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
```

### ROC / AUC

Evaluation reports the **ROC curve** and **AUC** per fold and overall (`ROC_CrossVal.py` uses `sklearn.metrics.roc_auc_score`). Results are saved per fold under `results/<marker>/.../Fold_<i>/ROC.png`, plus an aggregate `ROC.png` at the run root.

## 6. Frontend + Backend

- **Frontend** — React + TypeScript + Vite, Tailwind CSS, Recharts. Dev server on `http://localhost:5173`.
- **Backend** — FastAPI (auto-generated OpenAPI docs at `http://localhost:8000/docs`), served by Uvicorn on `http://localhost:8000`. CORS allows the frontend origin.
- The ML service launches `RUN_PROJECT.py` from the backend and streams training logs; results (metrics, ROC images) are served back to the frontend via REST endpoints.

## 7. Demo Dataset

The repository ships with a **SYNTHETIC DEMO DATASET** generated by `generate_demo_data.py`. It is intended to validate the end-to-end pipeline, not to produce clinical results.

| Property | Value |
|----------|-------|
| Dataset type | **Synthetic Demo Dataset** (not real clinical data) |
| Total samples | 40 patients (bags) |
| Class balance | 20 class-0, 20 class-1 |
| Feature dimension | 512 (matches `--featssize 512`) |
| Tiles per bag | 200 |
| Feature location | `demo_feats/patient_000.pt` ... `patient_039.pt` |
| Label map | `Path.csv` (no header, columns: `path, label`) |

## 8. Results

On the **synthetic demo dataset**, the MIL pipeline achieves **AUC = 1.0**. Because the synthetic bags are linearly separable by construction (class means separated by a fixed offset), this result reflects **DEMO / PIPELINE VALIDATION ONLY**:

- 🔸 AUC 1.0 is **DEMO/PIPELINE VALIDATION ONLY**.
- 🔸 It is **not** a clinical result and not generalizable to real histopathology.
- 🔸 The dataset contains no real patient tissue.
- 🔸 See `docs/results.png` for the demo ROC curve.

Real-data performance is expected to differ substantially and is not represented by these numbers.

## 9. Explainability

DSMIL provides **instance-level attention weights** via the attention matrix `A` returned by `BClassifier.forward`. These attention scores highlight the patches that most influenced the slide-level (bag) prediction, yielding interpretable, attention-based localization of subtype-relevant regions — in line with attention-based MIL ([Ilse et al., 2018](#research-paper--reference)).

## 10. Project Structure

```
ContrastiveVirtualStaining-main/
├── config.yaml              # training config (dsmil, lr=2e-4, epochs, dropout, BCE)
├── train.py                 # DSMIL training + 5-fold CV loop
├── RUN_PROJECT.py           # single-entry runner -> train.py
├── generate_demo_data.py    # creates the synthetic demo dataset
├── dsmil.py                 # DSMIL model (FCLayer, BClassifier, MILNet)
├── Train_Test_Splitter.py   # 5-fold stratified patient-level split
├── ROC_CrossVal.py          # cross-validation ROC/AUC evaluation
├── Path.csv                 # demo dataset label map (path,label)
├── init.pth                 # initial DSMIL state-dict checkpoint
├── environment.yaml         # conda environment
├── LICENSE.txt              # CC license
├── frontend/                # React + TypeScript + Vite dashboard (:5173)
│   └── src/{api,components,pages}
├── backend/                 # FastAPI service (:8000)
│   ├── main.py
│   ├── requirements.txt
│   ├── api/routes.py
│   └── services/ml_service.py
├── demo_feats/              # 40 synthetic feature bags (.pt)
└── results/                 # checkpoints, configs, ROC curves
```

## 11. Installation & Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### ML (Python)

The training code depends on PyTorch, scikit-learn, pandas, and matplotlib. `environment.yaml` defines the conda environment:

```bash
conda env create -f environment.yaml
conda activate contrastive-virtual-staining
```

## 12. How to Run ML

The demo data ships pre-generated. To (re)generate it and run the full experiment:

```bash
python generate_demo_data.py   # (re)create synthetic demo features
python RUN_PROJECT.py          # runs 5-fold DSMIL training + ROC/AUC
```

`RUN_PROJECT.py` invokes `train.py` with:

```
--dataset KRT --featssize 512 --seed 42 --Folds 5 --augment False
--optimizer AdamW --sampling default --env local --balancedSampler over --featsExtractor UNI
```

Results and ROC curves are written under `results/`.

## 13. How to Run Backend

```bash
cd backend
uvicorn backend.main:app --reload --port 8000
```

The API then listens on `http://localhost:8000` (interactive docs at `http://localhost:8000/docs`).

## 14. How to Run Frontend

```bash
cd frontend
npm run dev
```

Open the dashboard at **http://localhost:5173**.

## 15. API

Base URL: `http://localhost:8000` (frontend calls `http://localhost:8000/api`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check. |
| GET | `/api/project` | Project title, problem, solution, disclaimer. |
| GET | `/api/config` | Training configuration (`config.yaml`). |
| GET | `/api/dataset` | Demo dataset summary (counts, feature dim, type). |
| GET | `/api/patients` | Per-patient path, label, and file existence. |
| GET | `/api/results` | List of past experiment runs. |
| GET | `/api/results/latest` | Latest run metrics and ROC availability. |
| GET | `/api/results/roc` | Aggregate ROC image (`ROC.png`). |
| GET | `/api/results/roc/fold/{fold_idx}` | Per-fold ROC image. |
| GET | `/api/run/status` | Live status/log of an in-progress experiment. |
| POST | `/api/run` | Start an experiment (`{"mode": "demo"}`). |

OpenAPI UI: http://localhost:8000/docs

## 16. Limitations

- **Synthetic demo data only.** The bundled dataset is generated programmatically and contains **no real patient data**.
- **AUC 1.0 is not a clinical result.** It is an artifact of trivially separable synthetic data and serves only to validate that the pipeline runs end-to-end.
- **Precomputed features only.** This repo performs downstream MIL classification/evaluation on precomputed embeddings; the full feature-extraction encoders (ResNet18 / UNI) are external and not bundled.
- **No virtual-staining generator.** The complete contrastive virtual-staining model is **not included**; this repository focuses on the downstream subtype classification step.
- Small sample size (40 bags) makes statistics unstable and unsuitable for clinical inference.

## 17. Future Work

- Integrate real H&E patch features (and the trained ResNet18 / UNI encoders) to train on clinical data.
- Add the contrastive virtual-staining generator for end-to-end H&E→synthetic-IHC translation.
- Expand from binary KRT/HNF1A tasks to the full 3-class (KRT81+/HNF1A+/double-negative) PDAC subtyping scheme.
- Run on larger, multi-center cohorts with external validation.
- Replace synthetic AUC reporting with real cross-validation statistics and confidence intervals.

## 18. Research Paper / Reference

This work accompanies the paper:

> **Contrastive virtual staining enhances deep learning-based PDAC subtyping from H&E-stained tissue cores.** Manuelische Fischer, Alexander Muckenhuber, Robin Peretzke, Luay Farah, Constantin Ulrich, Sebastian Ziegler, Philipp Schader, Lorenz Feineis, Hanno Gao, Shuhan Xiao, Michael Götz, Marco Nolden, Katja Steiger, Jens T. Sieveke, Lukas Endrös, Rickmer Braren, Jens Kleesiek, Peter Schüffler, Peter Neher, Klaus Maier-Hein.

Key references used by the pipeline:

```bibtex
@inproceedings{li2021dual,
  title={Dual-stream multiple instance learning network for whole slide image classification with self-supervised contrastive learning},
  author={Li, Bin and Li, Yin and Eliceiri, Kevin W},
  booktitle={Proceedings of the IEEE/CVF conference on computer vision and pattern recognition},
  pages={14318--14328},
  year={2021}
}

@inproceedings{ilse2018attention,
  title={Attention-based deep multiple instance learning},
  author={Ilse, Maximilian and Tomczak, Jakub and Welling, Max},
  booktitle={International conference on machine learning},
  pages={2127--2136},
  year={2018},
  organization={PMLR}
}

@article{chen2024towards,
  title={Towards a general-purpose foundation model for computational pathology},
  author={Chen, Richard J and Ding, Tong and Lu, Ming Y and Williamson, Drew FK and Jaume, Guillaume and Song, Andrew H and Chen, Bowen and Zhang, Andrew and Shao, Daniel and Shaban, Muhammad and others},
  journal={Nature Medicine},
  volume={30},
  number={3},
  pages={850--862},
  year={2024},
  publisher={Nature Publishing Group}
}
```

## 19. Academic Disclaimer

This software is a **research prototype** developed in an academic setting. It has not been validated for clinical use, is not FDA/CE approved, and should not be used for patient diagnosis, treatment decisions, or any clinical workflow. All results shown are on synthetic demo data only. The German Cancer Research Center (DKFZ) and contributors assume no liability for clinical use.

Copyright German Cancer Research Center (DKFZ) and contributors. See `LICENSE.txt`.

<img src="docs/dkfz_logo.png" height="80" />

---

*Awarded partial funding: this work was partially funded by the Research Campus M2OLIE, supported by the German Federal Ministry of Education and Research (BMBF) under funding code 13GW0388A.*
