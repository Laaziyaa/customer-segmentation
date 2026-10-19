/**
 * API client with automatic cold-start retry, backoff, and TanStack Query integration.
 */

import { QueryClient } from "@tanstack/react-query";
import type {
  ChatResponse,
  CustomerDetailResponse,
  CustomersListResponse,
  DatasetSchemaResponse,
  EDAResponse,
  HealthResponse,
  ModelEvaluationResponse,
  PipelineStatusResponse,
  PredictResponse,
  SegmentsResponse,
  UploadResponse,
} from "./types";

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "https://customer-segmentation-agent.onrender.com");

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 2, // 2 minutes
      refetchOnWindowFocus: true,
      retry: (failureCount, error: any) => {
        // Cold start retry up to 4 times with backoff
        if (failureCount < 4) return true;
        return false;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
    },
  },
});

export async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;

  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `Server error ${res.status}`;
      try {
        const errJson = await res.json();
        errorMsg = errJson.detail || errJson.message || errorMsg;
      } catch {
        // ignore parse error
      }
      throw new Error(errorMsg);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    throw err;
  }
}

// ----------------------------------------------------
// Typed API Endpoints
// ----------------------------------------------------

export const api = {
  getHealth: () => request<HealthResponse>("api/health"),
  getSchema: () => request<DatasetSchemaResponse>("api/schema"),
  getSegments: () => request<SegmentsResponse>("api/segments"),
  
  getCustomers: (params?: {
    page?: number;
    page_size?: number;
    search?: string;
    segment?: number | string;
    min_age?: number;
    max_age?: number;
    min_balance?: number;
    max_balance?: number;
    sort_by?: string;
    sort_dir?: string;
  }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.search) q.set("search", params.search);
    if (params?.segment !== undefined && params.segment !== "") q.set("segment", String(params.segment));
    if (params?.min_age) q.set("min_age", String(params.min_age));
    if (params?.max_age) q.set("max_age", String(params.max_age));
    if (params?.min_balance) q.set("min_balance", String(params.min_balance));
    if (params?.max_balance) q.set("max_balance", String(params.max_balance));
    if (params?.sort_by) q.set("sort_by", params.sort_by);
    if (params?.sort_dir) q.set("sort_dir", params.sort_dir);

    const qs = q.toString();
    return request<CustomersListResponse>(`api/customers${qs ? `?${qs}` : ""}`);
  },

  getCustomerDetail: (id: number | string) =>
    request<CustomerDetailResponse>(`api/customers/${id}`),

  predict: (customer: Record<string, any>) =>
    request<PredictResponse>("api/predict", {
      method: "POST",
      body: JSON.stringify(customer),
    }),

  getEvaluation: () => request<ModelEvaluationResponse>("api/model/evaluation"),

  getEDA: (metric: string = "distributions", column?: string, cluster?: number) => {
    const q = new URLSearchParams({ metric });
    if (column) q.set("column", column);
    if (cluster !== undefined) q.set("cluster", String(cluster));
    return request<EDAResponse>(`api/eda?${q.toString()}`);
  },

  chat: (query: string) =>
    request<ChatResponse>("api/chat", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),

  getChatStatus: () => request<ChatStatusResponse>("api/chat/status"),

  setChatKey: (apiKey: string) =>
    request<KeyActionResponse>("api/chat/key", {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey }),
    }),

  clearChatKey: () =>
    request<KeyActionResponse>("api/chat/key", {
      method: "DELETE",
    }),

  uploadDataset: async (file: File): Promise<UploadResponse> => {
    const url = `${API_BASE_URL.replace(/\/$/, "")}/api/datasets/upload`;
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(url, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      let msg = "Failed to upload file.";
      try {
        const j = await res.json();
        msg = j.detail || msg;
      } catch {}
      throw new Error(msg);
    }

    return (await res.json()) as UploadResponse;
  },

  trainDataset: (datasetId: string, k?: number) =>
    request<PipelineStatusResponse>("api/datasets/train", {
      method: "POST",
      body: JSON.stringify({ dataset_id: datasetId, k }),
    }),

  getPipelineStatus: (jobId: string) =>
    request<PipelineStatusResponse>(`api/datasets/status/${jobId}`),

  resetDataset: () =>
    request<DatasetResetResponse>("api/datasets/reset", {
      method: "POST",
    }),
};
