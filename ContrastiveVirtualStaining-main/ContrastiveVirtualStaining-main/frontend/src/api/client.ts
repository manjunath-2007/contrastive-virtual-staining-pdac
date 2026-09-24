import axios from "axios";

const api = axios.create({ baseURL: "http://localhost:8000/api" });

export const getHealth = () => api.get("/health");
export const getProject = () => api.get("/project");
export const getConfig = () => api.get("/config");
export const getDataset = () => api.get("/dataset");
export const getPatients = () => api.get("/patients");
export const getResults = () => api.get("/results");
export const getLatestResult = () => api.get("/results/latest");
export const getRunStatus = () => api.get("/run/status");
export const postRun = (mode: string) => api.post("/run", { mode });

export const rocUrl = () => `http://localhost:8000/api/results/roc?t=${Date.now()}`;
export const foldRocUrl = (fold: number) =>
  `http://localhost:8000/api/results/roc/fold/${fold}?t=${Date.now()}`;

export default api;
