import { apiBaseUrl } from "./config";

export type ValidationJobState =
  | "queued" | "running" | "cancelling" | "finished" | "cancelled" | "failed";

export interface ValidationPreview {
  upload_id: string;
  total: number;
  columns: string[];
  preview: { question: string; expected: string }[];
}

export interface ValidationJob {
  job_id: string;
  state: ValidationJobState;
  total: number;
  completed: number;
  rows: { index: number; question: string; status: string; duration: number | null }[];
}

async function asError(response: Response): Promise<Error> {
  let message = "批量评测请求失败，请检查服务连接。";
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body
      && typeof body.detail === "string") message = body.detail;
  } catch { /* Non-JSON response */ }
  return new Error(message);
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiBaseUrl + url, init);
  if (!response.ok) throw await asError(response);
  return response.json() as Promise<T>;
}

export const validationBatchApi = {
  async preview(file: File): Promise<ValidationPreview> {
    const form = new FormData();
    form.append("file", file);
    return json("/api/validation-batches/preview", { method: "POST", body: form });
  },
  start(id: string): Promise<{ job_id: string; state: ValidationJobState; total: number }> {
    return json("/api/validation-batches/" + encodeURIComponent(id) + "/start", {
      method: "POST",
    });
  },
  status(id: string): Promise<ValidationJob> {
    return json("/api/validation-batches/jobs/" + encodeURIComponent(id));
  },
  cancel(id: string): Promise<{ state: ValidationJobState }> {
    return json("/api/validation-batches/jobs/" + encodeURIComponent(id) + "/cancel", {
      method: "POST",
    });
  },
  async download(id: string): Promise<void> {
    const response = await fetch(
      apiBaseUrl + "/api/validation-batches/jobs/" + encodeURIComponent(id) + "/export",
    );
    if (!response.ok) throw await asError(response);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const element = document.createElement("a");
    element.href = url;
    element.download = "guance-validation-results.xlsx";
    document.body.appendChild(element);
    element.click();
    element.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};
