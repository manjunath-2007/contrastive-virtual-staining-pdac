import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, BookOpen, Database, Cpu, FlaskConical,
  BarChart2, TrendingUp, GitBranch, Info,
} from "lucide-react";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/overview", icon: BookOpen, label: "Project Overview" },
  { to: "/dataset", icon: Database, label: "Dataset" },
  { to: "/model", icon: Cpu, label: "Model" },
  { to: "/experiment", icon: FlaskConical, label: "Experiment" },
  { to: "/results", icon: BarChart2, label: "Results" },
  { to: "/roc", icon: TrendingUp, label: "ROC Curve" },
  { to: "/methodology", icon: GitBranch, label: "Methodology" },
  { to: "/about", icon: Info, label: "About" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
      <div className="px-4 py-5 border-b border-gray-800">
        <div className="text-xs text-blue-400 font-semibold uppercase tracking-widest mb-1">PDAC Research</div>
        <div className="text-white font-bold text-sm leading-tight">Virtual Staining Dashboard</div>
      </div>
      <nav className="flex-1 py-4 px-2 space-y-0.5">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-blue-900 text-blue-200 font-medium"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-gray-800 text-xs text-gray-600">
        Research prototype · Not for clinical use
      </div>
    </aside>
  );
}
