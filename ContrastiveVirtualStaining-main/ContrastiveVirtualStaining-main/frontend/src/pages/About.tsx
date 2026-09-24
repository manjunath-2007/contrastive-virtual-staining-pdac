import { Card, SectionTitle, Disclaimer } from "../components/UI";

export default function About() {
  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">About</h1>
      <Disclaimer text="Research prototype — not for clinical diagnosis." />

      <Card>
        <SectionTitle>Project</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed">
          This project explores using <strong className="text-white">contrastive virtual staining</strong> to
          enhance deep learning-based classification of Pancreatic Ductal Adenocarcinoma (PDAC) subtypes from
          H&E-stained tissue cores. The goal is to predict molecular subtypes (KRT81+ and HNF1A+) without
          requiring additional immunohistochemistry (IHC) staining.
        </p>
      </Card>

      <Card>
        <SectionTitle>Paper</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed">
          This codebase accompanies the research on contrastive virtual staining for PDAC subtyping. The
          original approach trains a contrastive model to generate virtual IHC feature vectors from H&E images,
          which are then fed into a DSMIL classifier to predict subtypes. In this repository, pre-computed
          feature vectors are used directly — the virtual staining model itself is not included.
        </p>
      </Card>

      <Card>
        <SectionTitle>Dataset</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed">
          The demo dataset consists of synthetic feature vectors derived from tissue core slides. It is used solely
          to validate the end-to-end pipeline (feature loading → DSMIL training → 5-fold cross-validation → ROC/AUC
          evaluation). It does not represent real patient data and should not be used for clinical inference.
        </p>
      </Card>

      <Card>
        <SectionTitle>Method</SectionTitle>
        <p className="text-gray-400 text-sm leading-relaxed">
          Each tissue core is treated as a bag of 256×256 patches in a Multiple Instance Learning (MIL) framework.
          DSMIL uses a dual-stream architecture (instance + bag) with attention aggregation. Classification is
          performed with 5-fold cross-validation, and performance is reported via AUC, accuracy, precision, recall,
          and F1 score.
        </p>
      </Card>

      <Card>
        <SectionTitle>Limitations</SectionTitle>
        <p className="text-yellow-400 text-sm leading-relaxed">
          This is a research prototype intended for academic exploration. It has not been validated for clinical
          use. Predictions are based on a synthetic demo dataset and the full virtual staining pipeline (feature
          extraction from raw H&E) is not implemented in this repository.
        </p>
      </Card>
    </div>
  );
}
