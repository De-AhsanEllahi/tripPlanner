import { api } from "./client";

export const getTrips = async () => {
  const res = await api.get("/api/trips/");
  return res.data;
};

export const createTrip = async (data: any) => {
  const res = await api.post("/api/trips/", data);
  return res.data;
};