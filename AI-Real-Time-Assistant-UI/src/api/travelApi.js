import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
  headers: {
    "Content-Type": "application/json",
  },
});

export const createTravelPlan = async (payload) => {
  const response = await apiClient.post("/travel/plan", payload);
  return response.data;
};

export const checkBackendHealth = async () => {
  const response = await apiClient.get("/health");
  return response.data;
};

export const getTravelTools = async () => {
  const response = await apiClient.get("/travel/tools");
  return response.data;
};

export default apiClient;
