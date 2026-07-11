export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8020";

type RequestOptions = {
  token?: string | null;
};

function authHeaders(token?: string | null): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(options.token),
    cache: "no-store"
  });
  return parseResponse<T>(response);
}

export async function apiPost<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(options.token)
  });
  return parseResponse<T>(response);
}

export async function apiPostJson<T>(
  path: string,
  payload: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(options.token)
    },
    body: JSON.stringify(payload)
  });
  return parseResponse<T>(response);
}

export async function apiPostForm<T>(
  path: string,
  form: FormData,
  options: RequestOptions = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(options.token),
    body: form
  });
  return parseResponse<T>(response);
}

export function downloadReportUrl(taskId: string, format: "md" | "pdf"): string {
  return `${API_BASE}/api/tasks/${taskId}/report.${format}`;
}

export async function downloadReportFile(
  taskId: string,
  format: "md" | "pdf",
  token?: string | null
): Promise<void> {
  const response = await fetch(downloadReportUrl(taskId, format), {
    headers: authHeaders(token)
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = `sales-report-${taskId}.${format}`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
