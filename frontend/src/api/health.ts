import api from "./client";

export const getHealth = async () => {
  const response = await api.get("/api/health/");
  return response.data;
};