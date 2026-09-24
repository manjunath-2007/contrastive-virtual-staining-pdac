import { useEffect, useState } from "react";
import { getLatestResult, rocUrl, foldRocUrl } from "../api/client";
import { Card, SectionTitle, Disclaimer, MetricCard } from "../components/UI";

export default function ROC() {
  const [latest, setLatest] = useState<any>(null);
  const [error, setError] = useState("");
  const [rocKey, setRocKey] = useState(Date.now());

  useEffect(() => {
    getLatestResult()
      .then(r => { setLatest(r.data); setRocKey(Date.now()); })
      .catch(() => setError("No results found. Run an experiment first."));
  }, []);

  const m = latest?.metrics ?? {};
  const na = "Not available";

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">ROC Curve</h1>
      <Disclaimer text="Demo Dataset — Synthetic Data. ROC curves are for pipeline validation only, not clinical performance." />

      {error && (
        <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 text-gray-400 text-center">
          {error}
        </div>
      )}

      {latest && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <MetricCard label="AUC" value={m.auc != null ? m.auc.toFixed(3) : na} />
            <MetricCard label="Accuracy" value={m.accuracy != null ? (m.accuracy * 100).toFixed(1) + "%" : na} />
            <MetricCard label="Precision" value={m.precision != null ? m.precision.toFixed(3) : na} />
            <MetricCard label="Recall" value={m.recall != null ? m.recall.toFixed(3) : na} />
            <MetricCard label="F1" value={m.f1 != null ? m.f1.toFixed(3) : na} />
          </div>

          <Card>
            <SectionTitle>ROC Curve — Cross-Validation</SectionTitle>
            {latest.roc_exists ? (
              <img
                key={rocKey}
                src={rocUrl()}
                alt="ROC Curve"
                className="rounded-lg max-w-full border border-gray-700"
              />
            ) : (
              <p className="text-gray-500 text-sm">ROC.png not found in latest result folder.</p>
            )}
          </Card>

          <Card>
            <SectionTitle>Per-Fold ROC Curves</SectionTitle>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Array.from({ length: latest.fold_count }, (_, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-2">
                  <div className="text-xs text-gray-500 mb-1">Fold {i}</div>
                  <img
                    src={foldRocUrl(i)}
                    alt={`Fold ${i} ROC`}
                    className="rounded w-full"
                    onError={e => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <SectionTitle>What is ROC?</SectionTitle>
            <p className="text-gray-400 text-sm leading-relaxed">
              The Receiver Operating Characteristic (ROC) curve plots the True Positive Rate (Sensitivity)
              against the False Positive Rate (1 − Specificity) at various classification thresholds.
              The Area Under the Curve (AUC) measures overall performance: AUC = 1.0 is perfect,
              AUC = 0.5 is equivalent to random guessing.
            </p>
          </Card>
        </>
      )}
    </div>
  );
}