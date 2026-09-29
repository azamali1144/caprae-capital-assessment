export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type Query = Record<string, string | number | boolean | string[] | null | undefined>;

export function buildUrl(path: string, query?: Query): string {
  const url = new URL(API_URL + path);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) value.forEach((v) => url.searchParams.append(key, v));
    else url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function request<T>(path: string, init: RequestInit & { query?: Query } = {}): Promise<T> {
  const { query, ...rest } = init;
  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), rest);
  } catch {
    throw new ApiError(0, "NETWORK_ERROR", "Can't reach the LeadLens API. Is the backend running?");
  }

  if (!res.ok) {
    // backend always answers with {error: {code, message}}
    let code = "HTTP_ERROR";
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? body?.detail ?? message;
    } catch {
      /* not json, keep the defaults */
    }
    throw new ApiError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const json = (body: unknown): RequestInit => ({
  body: JSON.stringify(body),
  headers: { "Content-Type": "application/json" },
});

export const apiGet = <T>(path: string, query?: Query) => request<T>(path, { query });

export const apiPost = <T>(path: string, body?: unknown, query?: Query) =>
  request<T>(path, { method: "POST", query, ...(body === undefined ? {} : json(body)) });

export const apiPatch = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PATCH", ...json(body) });

export const apiPut = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PUT", ...json(body) });

export const apiUpload = <T>(path: string, form: FormData) =>
  request<T>(path, { method: "POST", body: form });
