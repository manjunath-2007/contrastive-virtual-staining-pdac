import { useEffect, useState } from "react";
import { getConfig } from "../api/client";
import { Card, SectionTitle, PipelineStep } from "../components/UI";

export default function ModelPage() {
  const [config, setConfig] = useState<any>(null);

  useEffect(() => {
    getConfig().then(r => setConfig(r.data)).catch(() => {});
  }, []);

  const cfg = config ?? {};
  const args = cfg.args ?? {};

  const params = [
    { label: "Model", value: cfg.model ?? "dsmil" },
    { label: "Dataset", value: args.dataset ?? "KRT" },
    { label: "Feature Size", value: args.featssize ?? "512" },
    { label: "Folds", value: args.Folds ?? "5" },
    { label: "Epochs", value: cfg.num_epochs ?? "5" },
    { label: "Optimizer", value: args.optimizer ?? "AdamW" },
    { label: "Learning Rate", value: cfg.lr ?? "0.0002" },
    { label: "Weight Decay", value: cfg.weight_decay ?? "0.001" },
    { label: "Criterion", value: cfg.criterion ?? "BCE" },
    { label: "Augmentation", value: args.augment ?? "False" },
    { label: "Balanced Sampler", value: args.balancedSampler ?? "over" },
    { label: "Dropout (patch)", value: cfg.dropout_patch ?? "0.0" },
    { label: "Dropout (node)", value: cfg.dropout_node ?? "0.0" },
    { label: "Non-linearity", value: cfg.non_linearity ?? "1" },
  ];

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">Model Architecture</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <SectionTitle>DSMIL — Dual-Stream MIL</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed mb-4">
            DSMIL (Dual-Stream Multiple Instance Learning) is designed for computational pathology.
            It processes tissue cores as bags of patch features and uses two parallel streams:
          </p>
          <ul className="space-y-2 text-sm">
            <li className="flex gap-2">
              <span className="text-blue-400 font-semibold shrink-0">Instance Stream:</span>
              <span className="text-gray-400">Evaluates each patch independently to find the most discriminative regions.</span>
            </li>
            <li className="flex gap-2">
              <span className="text-green-400 font-semibold shrink-0">Bag Stream:</span>
              <span className="text-gray-400">Aggregates all patch information using attention to produce a bag-level prediction.</span>
            </li>
          </ul>
          <p className="text-gray-500 text-xs mt-3">
            Final prediction = 0.5 × instance prediction + 0.5 × bag prediction
          </p>
        </Card>

        <Card>
          <SectionTitle>How the Model Decides</SectionTitle>
          <div className="flex flex-col items-start">
            {[
              "Tissue Core",
              "Multiple Patches / Feature Vectors",
              "Patch-level Importance (Instance Stream)",
              "Bag-level Aggregation (Bag Stream)",
              "DSMIL Fusion",
              "PDAC Subtype Prediction",
            ].map((s, i, arr) => (
              <PipelineStep key={s} label={s} last={i === arr.length - 1} />
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <SectionTitle>Current Configuration</SectionTitle>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {params.map(({ label, value }) => (
            <div key={label} className="bg-gray-800 rounded-lg p-3">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</div>
              <div className="text-white font-semibold text-sm">{String(value)}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-600 mt-3">Values read from config.yaml and RUN_PROJECT.py</p>
      </Card>

      <Card>
        <SectionTitle>Multiple Instance Learning (MIL)</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed">
          In standard supervised learning, each sample has a label. In MIL, a <em>bag</em> (tissue core)
          contains multiple <em>instances</em> (patches). Only the bag has a label — not individual patches.
          This is ideal for pathology because annotating every patch is impractical.
          DSMIL learns which patches are most important for the final classification.
        </p>
      </Card>
    </div>
  );
}
