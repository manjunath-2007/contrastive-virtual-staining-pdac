import { Card, PipelineStep, SectionTitle, Disclaimer } from "../components/UI";

export default function Overview() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">Project Overview</h1>
      <Disclaimer text="Research prototype — not for clinical diagnosis." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <SectionTitle>The Problem</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed">
            Pancreatic Ductal Adenocarcinoma (PDAC) has two main molecular subtypes:
          </p>
          <ul className="mt-2 space-y-1 text-sm">
            <li className="text-blue-300">• <strong>KRT81+</strong> — Squamous/Basal-like subtype (worse prognosis)</li>
            <li className="text-green-300">• <strong>HNF1A+</strong> — Classical/Exocrine-like subtype (better prognosis)</li>
          </ul>
          <p className="text-gray-400 text-sm mt-3 leading-relaxed">
            Standard H&E staining alone cannot reliably distinguish these subtypes.
            Additional IHC (immunohistochemistry) staining is expensive and time-consuming.
          </p>
        </Card>

        <Card>
          <SectionTitle>The Solution</SectionTitle>
          <p className="text-gray-400 text-sm leading-relaxed">
            Use <strong className="text-white">contrastive learning</strong> to train a model that generates
            virtual IHC staining representations from H&E images. These virtual features are then used
            by <strong className="text-white">DSMIL</strong> to classify PDAC subtypes without requiring
            actual IHC staining.
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <SectionTitle>Full Paper Concept</SectionTitle>
          <div className="flex flex-col items-start gap-0">
            {[
              "H&E-Stained Tissue Core",
              "Contrastive Virtual Staining Model",
              "Virtual KRT81 / HNF1A Features",
              "DSMIL (MIL Classifier)",
              "PDAC Subtype Prediction",
              "ROC / AUC Evaluation",
            ].map((s, i, arr) => (
              <PipelineStep key={s} label={s} last={i === arr.length - 1} />
            ))}
          </div>
        </Card>

        <Card>
          <SectionTitle>Current Repository Implementation</SectionTitle>
          <div className="flex flex-col items-start gap-0">
            {[
              "Path.csv + Feature Files (.pt)",
              "Pre-computed Feature Vectors (512-dim)",
              "DSMIL Classifier",
              "5-Fold Cross Validation",
              "PDAC Subtype Classification",
              "ROC / AUC Evaluation",
            ].map((s, i, arr) => (
              <PipelineStep key={s} label={s} last={i === arr.length - 1} />
            ))}
          </div>
          <p className="text-yellow-400 text-xs mt-3">
            Note: The contrastive virtual staining step (feature extraction) is not included in this repository.
            Pre-computed features are used directly.
          </p>
        </Card>
      </div>

      <Card>
        <SectionTitle>Key Concepts</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          {[
            { term: "MIL", def: "Multiple Instance Learning — a tissue core is treated as a 'bag' of patches. The model learns from bag-level labels without needing patch-level annotations." },
            { term: "DSMIL", def: "Dual-Stream MIL — uses both instance-level and bag-level classifiers. The dual stream helps capture both local patch information and global tissue context." },
            { term: "ROC / AUC", def: "Receiver Operating Characteristic curve. AUC (Area Under Curve) measures classification quality. AUC=1.0 is perfect; AUC=0.5 is random." },
          ].map(({ term, def }) => (
            <div key={term} className="bg-gray-800 rounded-lg p-3">
              <div className="text-blue-300 font-semibold mb-1">{term}</div>
              <div className="text-gray-400 text-xs leading-relaxed">{def}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
