export type SessionSummary = {
  id: string;
  user_id: string;
  title: string;
  provider: string;
  model: string;
  user_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type SessionList = { items: SessionSummary[]; total: number };
type ApiErrorPayload = { error?: { code?: string; message?: string; request_id?: string } };

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "unknown_error",
    readonly requestId?: string
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers }
    });
  } catch {
    throw new ApiError("The API is unavailable. Start FastAPI and PostgreSQL, then retry.", 0, "offline");
  }
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new ApiError(
      payload.error?.message ?? "The request could not be completed.",
      response.status,
      payload.error?.code,
      payload.error?.request_id
    );
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const listSessions = (): Promise<SessionList> =>
  request("/api/v1/sessions?user_id=local-evaluator");

export const createSession = (): Promise<SessionSummary> =>
  request("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ user_id: "local-evaluator", title: "New conversation" })
  });

export const addMessage = (sessionId: string, content: string): Promise<void> =>
  request(`/api/v1/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content })
  });

