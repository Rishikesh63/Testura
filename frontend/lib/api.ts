import axios from "axios";
import { supabase } from "./supabase";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session?.access_token) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

export const repoApi = {
  list: () => api.get("/repos"),
  connect: (repoUrl: string) => api.post("/repos", { repo_url: repoUrl }),
  get: (id: string) => api.get(`/repos/${id}`),
  delete: (id: string) => api.delete(`/repos/${id}`),
};

export const testApi = {
  run: (repoId: string) => api.post(`/repos/${repoId}/runs`),
  listRuns: (repoId: string) => api.get(`/repos/${repoId}/runs`),
  getRun: (repoId: string, runId: string) =>
    api.get(`/repos/${repoId}/runs/${runId}`),
};

export const billingApi = {
  createOrder: (plan: string, userId: string) =>
    api.post("/billing/create-order", { plan, user_id: userId }),
  verify: (data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
    plan: string;
    user_id: string;
  }) => api.post("/billing/verify", data),
  getPlan: (userId: string) => api.get(`/billing/plan/${userId}`),
};

export default api;
