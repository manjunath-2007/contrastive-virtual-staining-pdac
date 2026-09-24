export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-5 ${className}`}>
      {children}
    </div>
  );
}

export function Badge({ label, color = "blue" }: { label: string; color?: string }) {
  const colors: Record<string, string> = {
    blue: "bg-blue-900 text-blue-300 border-blue-700",
    green: "bg-green-900 text-green-300 border-green-700",
    yellow: "bg-yellow-900 text-yellow-300 border-yellow-700",
    red: "bg-red-900 text-red-300 border-red-700",
    gray: "bg-gray-800 text-gray-400 border-gray-600",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded border font-medium ${colors[color] ?? colors.blue}`}>
      {label}
    </span>
  );
}

export function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col gap-1">
      <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      <span className="text-2xl font-bold text-white">{value}</span>
      {sub && <span className="text-xs text-gray-500">{sub}</span>}
    </div>
  );
}

export function SectionTitle({ children }: { children: React.ReactNode }) {
  return <h2 className="text-lg font-semibold text-white mb-4">{children}</h2>;
}

export function Disclaimer({ text }: { text: string }) {
  return (
    <div className="bg-yellow-950 border border-yellow-800 rounded-lg px-4 py-3 text-yellow-300 text-sm">
      ⚠️ {text}
    </div>
  );
}

export function PipelineStep({ label, last = false }: { label: string; last?: boolean }) {
  return (
    <div className="flex flex-col items-center">
      <div className="bg-blue-900 border border-blue-700 text-blue-200 text-sm font-medium px-4 py-2 rounded-lg text-center min-w-[180px]">
        {label}
      </div>
      {!last && <div className="text-gray-500 text-xl leading-none my-1">↓</div>}
    </div>
  );
}
