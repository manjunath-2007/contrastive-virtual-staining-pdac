import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Overview from "./pages/Overview";
import DatasetPage from "./pages/DatasetPage";
import ModelPage from "./pages/ModelPage";
import ExperimentPage from "./pages/ExperimentPage";
import ResultsPage from "./pages/ResultsPage";
import ROC from "./pages/ROC";
import Methodology from "./pages/Methodology";
import About from "./pages/About";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="flex-1 bg-gray-950">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/overview" element={<Overview />} />
            <Route path="/dataset" element={<DatasetPage />} />
            <Route path="/model" element={<ModelPage />} />
            <Route path="/experiment" element={<ExperimentPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/roc" element={<ROC />} />
            <Route path="/methodology" element={<Methodology />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}