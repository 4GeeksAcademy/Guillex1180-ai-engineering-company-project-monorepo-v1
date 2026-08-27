import axios from "axios";

const configuredBaseURL = import.meta.env.VITE_API_BASE_URL?.trim();
const baseURL = import.meta.env.DEV ? "/" : configuredBaseURL || "/";

export const apiClient = axios.create({
  baseURL,
  timeout: 30000,
});
