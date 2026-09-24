import { useEffect, useState } from "react";
import { getDataset, getPatients } from "../api/client";
import { Card, SectionTitle, Disclaimer, Badge } from "../components/UI";

export default function DatasetPage() {
  const [info, setInfo] = useState<any>(null);
  const [patients, setPatients] = useState<any[]>([]);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    getDataset().then(r => setInfo(r.data)).catch(() => {});
    getPatients().then(r => setPatients(r.data.patients ?? [])).catch(() => {});
  }, []);

  const displayed = showAll ? patients : patients.slice(0, 15);

  return (
    <div className="p-6 space-y-6 max-w-5xl">
      <h1 className="text-xl font-bold text-white">Dataset</h1>
      <Disclaimer text="Current dataset: Synthetic Demo Dataset — not real patient biopsy data. Used for pipeline validation only." />

      {info && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "Total Samples", value: info.total_samples },
            { label: "Class 0 (KRT−)", value: info.class_0_count },
            { label: "Class 1 (KRT+)", value: info.class_1_count },
            { label: "Feature Dim", value: info.feature_dim ?? 512 },
            { label: "Feature Files", value: info.feature_files_count },
          ].map(({ label, value }) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wider">{label}</div>
              <div className="text-2xl font-bold text-white mt-1">{value}</div>
            </div>
          ))}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="text-xs text-gray-500 uppercase tracking-wider">Dataset Type</div>
            <div className="text-yellow-400 font-semibold mt-1 text-sm">Synthetic Demo</div>
          </div>
        </div>
      )}

      <Card>
        <SectionTitle>Patient / Feature File Table</SectionTitle>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-gray-500 text-xs uppercase">
                <th className="text-left py-2 pr-4">File</th>
                <th className="text-left py-2 pr-4">Label</th>
                <th className="text-left py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map((p, i) => (
                <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-2 pr-4 font-mono text-gray-300 text-xs">{p.file}</td>
                  <td className="py-2 pr-4">
                    <Badge
                      label={p.label === 0 ? "Class 0 (KRT−)" : "Class 1 (KRT+)"}
                      color={p.label === 0 ? "blue" : "green"}
                    />
                  </td>
                  <td className="py-2">
                    <Badge label={p.exists ? "Found" : "Missing"} color={p.exists ? "green" : "red"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {patients.length > 15 && (
          <button
            onClick={() => setShowAll(v => !v)}
            className="mt-3 text-blue-400 text-sm hover:underline"
          >
            {showAll ? "Show less" : `Show all ${patients.length} entries`}
          </button>
        )}
      </Card>
    </div>
  );
}
