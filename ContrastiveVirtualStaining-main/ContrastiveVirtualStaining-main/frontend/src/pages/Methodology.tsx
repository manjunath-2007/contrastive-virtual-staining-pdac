import { Card, PipelineStep, SectionTitle, Disclaimer } from "../components/UI";

export default function Methodology() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">Methodology</h1>
      <Disclaimer text="Research prototype — not for clinical diagnosis." />

      <Card>
        <SectionTitle>End-to-End Pipeline</SectionTitle>
        <div className="flex flex-col items-start gap-0">
          {[
            "H&E-Stained Tissue Cores (Whole Slide Images)",
            "Patch Extraction (256×256, non-overlapping)",
            "Contrastive Virtual Staining Model",
            "Virtual IHC Feature Vectors (512-dim, KRT81 / HNF1A)",
            "DSMIL Bag Formation (tissue core → bag of patches)",
            "5-Fold Cross-Validation Training",
            "PDAC Subtype Classification (KRT81+ vs HNF1A+)",
            "ROC / AUC Evaluation",
          ].map((s, i, arr) => (
            <PipelineStep key={s} label={s} last={i === arr.length - 1} />
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <SectionTitle>Contrastive Virtual Staining</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed mb-3">
            The core innovation of this research is using contrastive learning to train a model
            that transforms H&E-stained pathology images into virtual IHC representations.
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2">
              <span className="text-blue-400 font-semibold shrink-0">• Input:</span>
              <span className="text-gray-400">Standard H&E stained tissue cores from PDAC resections.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-semibold shrink-0">• Training:</span>
              <span className="text-gray-400">Contrastive loss pulls virtual features toward real IHC features of the same region and pushes away from others.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-blue-400 font-semibold shrink-0">• Output:</span>
              <span className="text-gray-400">512-dimensional virtual feature vectors that capture both KRT81 and HNF1A expression patterns.</span>
            </li>
          </ul>
        </Card>

        <Card>
          <SectionTitle>DSMIL — Dual-Stream MIL</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed mb-3">
            DSMIL (Dual-Stream Multiple Instance Learning) is designed for computational pathology
            where only bag-level (tissue core) labels are available.
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2">
              <span className="text-green-400 font-semibold shrink-0">• Instance Stream:</span>
              <span className="text-gray-400">Evaluates each patch independently, identifying the most discriminative regions.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-green-400 font-semibold shrink-0">• Bag Stream:</span>
              <span className="text-gray-400">Aggregates all patches using attention to produce a bag-level prediction.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-green-400 font-semibold shrink-0">• Fusion:</span>
              <span className="text-gray-400">Final prediction = 0.5 × instance + 0.5 × bag.</span>
            </li>
          </ul>
        </Card>
      </div>

      <Card>
        <SectionTitle>Cross-Validation Strategy</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed mb-3">
          The dataset is split into 5 folds. For each fold:
        </p>
        <ol className="space-y-1 text-sm text-gray-400 list-decimal list-inside">
          <li>4 folds are used for training (with a balanced sampler to handle class imbalance).</li>
          <li>1 fold is held out for evaluation.</li>
          <li>The process repeats 5 times so every sample is evaluated exactly once.</li>
          <li>Metrics (AUC, accuracy, precision, recall, F1) are averaged across all folds.</li>
        </ol>
      </Card>

      <Card>
        <SectionTitle>Current Repository Limitations</SectionTitle>
        <p className="text-yellow-400 text-sm">
          This repository implements the DSMIL classification pipeline only. The contrastive virtual staining
          model (feature extraction) is not included — pre-computed 512-dimensional feature vectors are used directly.
          To reproduce the full paper, the virtual staining model must be trained separately and used to
          generate features from raw H&E images.
        </p>
      </Card>
    </div>
  );
}