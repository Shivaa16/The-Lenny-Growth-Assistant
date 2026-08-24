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
export type SessionDetail = SessionSummary & { messages: Message[] };
type ApiErrorPayload = { error?: { code?: string; message?: string; request_id?: string } };

export type Message = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  status: "pending" | "completed" | "failed";
  model_metadata: Record<string, unknown>;
  created_at: string;
};

export type Citation = {
  position: number;
  chunk_id: string;
  title: string;
  guest: string;
  youtube_url: string | null;
  repository_path: string;
  quoted_text: string;
  relevance_score: number;
};

export type ConversationTurn = {
  user_message: Message;
  assistant_message: Message;
  citations: Citation[];
  grounded: boolean;
};

export type ProviderInfo = {
  provider: "ollama" | "anthropic";
  model: string;
  local_model: string;
  embedding_model: string;
  cloud_configured: boolean;
};

export type Artifact = {
  id: string;
  session_id: string;
  message_id: string | null;
  kind: "markdown" | "html";
  title: string;
  content: string;
  sanitized_content: string;
  artifact_metadata: {
    skill?: string;
    citations?: Array<{
      position: number;
      title: string;
      guest: string;
      youtube_url: string | null;
    }>;
    [key: string]: unknown;
  };
  created_at: string;
  updated_at: string;
};

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

export const getProviderInfo = (): Promise<ProviderInfo> => request("/api/v1/config");

export const getSession = (sessionId: string): Promise<SessionDetail> =>
  request(`/api/v1/sessions/${sessionId}`);

export const createSession = (): Promise<SessionSummary> =>
  request("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ user_id: "local-evaluator", title: "New conversation" })
  });

export const addMessage = (sessionId: string, content: string): Promise<ConversationTurn> =>
  request(`/api/v1/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content })
  });

export const createArtifact = (
  sessionId: string,
  topic: string,
  kind: Artifact["kind"] = "markdown"
): Promise<Artifact> =>
  request(`/api/v1/sessions/${sessionId}/artifacts`, {
    method: "POST",
    body: JSON.stringify({ topic, kind })
  });

export const listArtifacts = (sessionId: string): Promise<{ items: Artifact[] }> =>
  request(`/api/v1/sessions/${sessionId}/artifacts`);
