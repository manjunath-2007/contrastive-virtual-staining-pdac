import { useEffect, useState } from "react";
import { getDataset, getConfig, getLatestResult, getRunStatus } from "../api/client";
import { MetricCard, Disclaimer, Card, SectionTitle } from "../components/UI";

export default function Dashboard() {
  const [dataset, setDataset] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [latest, setLatest] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    getDataset().then(r => setDataset(r.data)).catch(() => {});
    getConfig().then(r => setConfig(r.data)).catch(() => {});
    getLatestResult().then(r => setLatest(r.data)).catch(() => {});
    getRunStatus().then(r => setStatus(r.data)).catch(() => {});
  }, []);

  const m = latest?.metrics ?? {};
  const na = "Not available";

  const statusColor: Record<string, string> = {
    IDLE: "text-gray-400",
    RUNNING: "text-yellow-400",
    COMPLETED: "text-green-400",
    FAILED: "text-red-400",
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl">
      <div>
        <h1 className="text-xl font-bold text-white leading-snug max-w-3xl">
          Contrastive Virtual Staining Enhances Deep Learning-Based PDAC Subtyping from H&E-Stained Tissue Cores
        </h1>
        <p className="text-gray-400 text-sm mt-1">Research Dashboard · Academic Prototype</p>
      </div>

      <Disclaimer text="Demo Dataset — Synthetic Data. Current results are for pipeline validation and are not clinical results." />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <MetricCard label="Samples" value={dataset?.total_samples ?? na} sub="demo dataset" />
        <MetricCard label="Folds" value={config?.args?.Folds ?? "5"} sub="cross-validation" />
        <MetricCard label="Epochs" value={config?.num_epochs ?? na} sub="per fold" />
        <MetricCard label="Feature Size" value={config?.args?.featssize ?? "512"} sub="dimensions" />
        <MetricCard label="AUC" value={m.auc != null ? m.auc.toFixed(3) : na} sub="cross-val" />
        <MetricCard label="Accuracy" value={m.accuracy != null ? (m.accuracy * 100).toFixed(1) + "%" : na} />
        <MetricCard label="Precision" value={m.precision != null ? m.precision.toFixed(3) : na} />
        <MetricCard label="Recall" value={m.recall != null ? m.recall.toFixed(3) : na} />
        <MetricCard label="F1" value={m.f1 != null ? m.f1.toFixed(3) : na} />
        <MetricCard label="Class 0" value={dataset?.class_0_count ?? na} sub="samples" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <SectionTitle>Problem</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed">
            PDAC (Pancreatic Ductal Adenocarcinoma) has distinct molecular subtypes (KRT81, HNF1A) that affect prognosis and treatment.
            Identifying these subtypes from standard H&E staining alone is challenging and typically requires additional IHC staining.
          </p>
        </Card>
        <Card>
          <SectionTitle>Proposed Solution</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed">
            Use AI-based contrastive virtual staining to generate virtual IHC representations from H&E images,
            then apply DSMIL (Dual-Stream Multiple Instance Learning) for automated PDAC subtype classification.
          </p>
        </Card>
        <Card>
          <SectionTitle>Current Dataset</SectionTitle>
          <p className="text-gray-400 text-sm">
            <span className="text-yellow-400 font-medium">Synthetic Demo Dataset</span> — {dataset?.total_samples ?? "?"} samples,
            {" "}{dataset?.class_0_count ?? "?"} class 0, {dataset?.class_1_count ?? "?"} class 1.
            Feature dimension: {dataset?.feature_dim ?? "512"}. Used for pipeline validation only.
          </p>
        </Card>
        <Card>
          <SectionTitle>Experiment Status</SectionTitle>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-bold ${statusColor[status?.status ?? "IDLE"]}`}>
              {status?.status ?? "IDLE"}
            </span>
          </div>
          {status?.start_time && (
            <p className="text-xs text-gray-500 mt-2">Started: {new Date(status.start_time).toLocaleString()}</p>
          )}
          {status?.end_time && (
            <p className="text-xs text-gray-500">Ended: {new Date(status.end_time).toLocaleString()}</p>
          )}
          {!latest && <p className="text-gray-500 text-sm mt-2">No results yet. Run an experiment first.</p>}
        </Card>
      </div>
    </div>
  );
}
