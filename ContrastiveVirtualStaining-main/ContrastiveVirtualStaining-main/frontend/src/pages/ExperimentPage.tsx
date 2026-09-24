import { useEffect, useRef, useState } from "react";
import { getRunStatus, postRun } from "../api/client";
import { Card, Disclaimer } from "../components/UI";

const STATUS_COLOR: Record<string, string> = {
  IDLE: "text-gray-400",
  RUNNING: "text-yellow-400 animate-pulse",
  COMPLETED: "text-green-400",
  FAILED: "text-red-400",
};

const STATUS_BG: Record<string, string> = {
  IDLE: "border-gray-700",
  RUNNING: "border-yellow-700 bg-yellow-950/20",
  COMPLETED: "border-green-700 bg-green-950/20",
  FAILED: "border-red-700 bg-red-950/20",
};

export default function ExperimentPage() {
  const [status, setStatus] = useState<any>({ status: "IDLE", log: [] });
  const [error, setError] = useState("");
  const logRef = useRef<HTMLDivElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = () => {
    getRunStatus()
      .then(r => setStatus(r.data))
      .catch(() => {});
  };

  useEffect(() => {
    fetchStatus();
    pollRef.current = setInterval(fetchStatus, 2000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [status.log]);

  const handleRun = async () => {
    setError("");
    try {
      await postRun("demo");
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? "Failed to start experiment.");
    }
  };

  const isRunning = status.status === "RUNNING";

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <h1 className="text-xl font-bold text-white">Run ML Experiment</h1>
      <Disclaimer text="This runs the existing RUN_PROJECT.py → train.py → DSMIL pipeline on the demo dataset." />

      <Card className={`border-2 ${STATUS_BG[status.status] ?? ""}`}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Experiment Status</div>
            <div className={`text-3xl font-bold ${STATUS_COLOR[status.status]}`}>{status.status}</div>
            {status.start_time && (
              <div className="text-xs text-gray-500 mt-1">
                Started: {new Date(status.start_time).toLocaleString()}
              </div>
            )}
            {status.end_time && (
              <div className="text-xs text-gray-500">
                Ended: {new Date(status.end_time).toLocaleString()}
              </div>
            )}
          </div>
          <button
            onClick={handleRun}
            disabled={isRunning}
            className={`px-8 py-4 rounded-xl font-bold text-lg transition-all ${
              isRunning
                ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40"
            }`}
          >
            {isRunning ? "⏳ Running..." : "▶ RUN ML EXPERIMENT"}
          </button>
        </div>
        {error && <div className="mt-3 text-red-400 text-sm">{error}</div>}
      </Card>

      <Card>
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-semibold text-white">Console Output</span>
          <span className="text-xs text-gray-500">{status.log?.length ?? 0} lines</span>
        </div>
        <div
          ref={logRef}
          className="bg-gray-950 rounded-lg p-3 h-80 overflow-y-auto font-mono text-xs text-green-300 space-y-0.5"
        >
          {status.log?.length === 0 ? (
            <span className="text-gray-600">No output yet. Click "RUN ML EXPERIMENT" to start.</span>
          ) : (
            status.log.map((line: string, i: number) => (
              <div key={i} className="leading-relaxed">{line || "\u00A0"}</div>
            ))
          )}
        </div>
      </Card>

      <Card>
        <div className="text-sm font-semibold text-white mb-3">What happens when you click Run</div>
        <ol className="space-y-1 text-sm text-gray-400 list-decimal list-inside">
          <li>FastAPI backend receives the request</li>
          <li>Executes <code className="text-blue-300">RUN_PROJECT.py</code> as a subprocess</li>
          <li>RUN_PROJECT.py calls <code className="text-blue-300">train.py</code> with the configured arguments</li>
          <li>DSMIL trains for 5 folds × 5 epochs on the demo dataset</li>
          <li>ROC.png and metrics are saved to <code className="text-blue-300">results/</code></li>
          <li>Results appear on the Results and ROC pages</li>
        </ol>
      </Card>
    </div>
  );
}
