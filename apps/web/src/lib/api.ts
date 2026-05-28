/* eslint-disable */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://docppt-backend.onrender.com";

let cachedPublicKey: string | null = null;

async function encryptRSA(text: string, pemKey: string): Promise<string> {
  const pemHeader = "-----BEGIN PUBLIC KEY-----";
  const pemFooter = "-----END PUBLIC KEY-----";
  const pemContents = pemKey
    .replace(pemHeader, "")
    .replace(pemFooter, "")
    .replace(/\s+/g, "");
  
  const binaryDerString = window.atob(pemContents);
  const binaryDer = new Uint8Array(binaryDerString.length);
  for (let i = 0; i < binaryDerString.length; i++) {
    binaryDer[i] = binaryDerString.charCodeAt(i);
  }

  const publicKey = await window.crypto.subtle.importKey(
    "spki",
    binaryDer.buffer,
    {
      name: "RSA-OAEP",
      hash: "SHA-256",
    },
    true,
    ["encrypt"]
  );

  const enc = new TextEncoder();
  const encryptedBuffer = await window.crypto.subtle.encrypt(
    {
      name: "RSA-OAEP",
    },
    publicKey,
    enc.encode(text)
  );

  const bytes = new Uint8Array(encryptedBuffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

async function getEncryptedGeminiKey(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const rawKey = sessionStorage.getItem("gemini_api_key");
  if (!rawKey) return null;

  try {
    if (!cachedPublicKey) {
      const res = await fetch(`${API_BASE_URL}/api/auth/public-key`);
      if (!res.ok) throw new Error("Failed to fetch public key");
      const data = await res.json();
      cachedPublicKey = data.public_key;
    }
    
    if (!cachedPublicKey) return null;
    return await encryptRSA(rawKey, cachedPublicKey);
  } catch (err) {
    console.error("Error encrypting Gemini API Key:", err);
    return null;
  }
}

/**
 * Custom error class for API failures
 */
export class ApiError extends Error {
  public status: number;
  public data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = "ApiError";
  }
}

/**
 * Generic fetch wrapper for API calls to the FastAPI backend.
 * Centralizes error handling and JSON parsing.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Default headers for JSON requests
  const headers = new Headers(options.headers || {});
  
  // Inject authorization token if it exists in local storage
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("docppt_token");
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    
    // Inject encrypted Gemini API key if present in sessionStorage
    if (!endpoint.includes("/api/auth/public-key")) {
      const encKey = await getEncryptedGeminiKey();
      if (encKey) {
        headers.set("X-Gemini-API-Key", encKey);
      }
    }
  }
  
  // If body is a string and no content-type is set, assume JSON
  // If body is FormData, do not set Content-Type (browser will set it with boundary)
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = "An unknown error occurred";
    let errorData = null;
    
    try {
      const errorJson = await response.json();
      errorMessage = errorJson.detail || errorMessage;
      errorData = errorJson;
    } catch {
      // Not JSON, try text
      try {
        errorMessage = await response.text() || response.statusText;
      } catch {
        errorMessage = response.statusText;
      }
    }
    
    throw new ApiError(response.status, errorMessage, errorData);
  }

  // Handle No Content (204)
  if (response.status === 204) {
    return null as unknown as T;
  }

  // Handle Binary streams (e.g. PPT export)
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/vnd.openxmlformats-officedocument.presentationml.presentation")) {
    return response.blob() as unknown as T;
  }

  // Handle JSON
  return response.json() as Promise<T>;
}

// ---------------------------------------------------------
// Types & Methods
// ---------------------------------------------------------

export type RecentSessionItem = {
  id: string;
  session_type: string;
  input_type: string;
  input_label: string;
  status: string;
  error_message?: string | null;
  created_at: string;
  completed_at: string | null;
  metrics: {
    word_count?: number;
    summary_ready?: boolean;
    total_slides?: number;
    total_flags?: number;
  };
};

// -----------------------------------------------
// Rewrite / AI-Likeness types (new in v2)
// -----------------------------------------------

export type AiLikenessScore = {
  score: number;          // 0–100
  band: "low" | "moderate" | "high";
  reasons: string[];      // human-readable explanation strings
};

export type SegmentRewriteResult = {
  segment_id: string;
  action: "pass_through" | "clean_only" | "rewrite";
  candidate_text: string | null;
  judge_verdict: "accepted" | "rejected_all" | null;
  rejection_reason: string | null;
  eval_scores: { similarity?: number } | null;
};

export type RewriteRequest = {
  session_id: string;
  tone_preset: TonePreset;
  intensity: "minimal" | "balanced" | "strong";
  segment_ids?: string[];   // optional: rewrite specific segments only
};

export type RewriteResponse = {
  session_id: string;
  results: SegmentRewriteResult[];
  total_rewritten: number;
  total_passed: number;
  total_failed: number;
};

export type TonePreset =
  | "presentation_concise"
  | "executive_polished"
  | "founder_clear"
  | "product_manager_direct"
  | "consulting_professional";

export type RewriteIntensity = "minimal" | "balanced" | "strong";

export type SafetyLabel =
  | "safe_replace"
  | "needs_shorter_option"
  | "manual_review";

export type PptSegmentV2 = PptSegmentData & {
  ai_likeness?: AiLikenessScore;
  safety_label?: SafetyLabel;
  role?: "title" | "subtitle" | "bullet" | "body" | "caption" | "table_cell" | "speaker_note";
};

export type PptSessionOutput = {
  total_slides: number;
  total_flags: number;
  slide_scores: Record<string, number>;
  slides: Record<string, PptSegmentV2[]>;
};

export type SessionDetailResponse = {
  session: {
    id: string;
    session_type: string;
    input_type: string;
    input_label: string | null;
    status: string;
    created_at: string | null;
    completed_at: string | null;
    error_message: string | null;
  };
  output: PptSessionOutput | null;
};

export const SessionAPI = {
  async getRecent(): Promise<RecentSessionItem[]> {
    return apiFetch<RecentSessionItem[]>("/api/sessions/recent");
  },
  async getDetail(sessionId: string): Promise<SessionDetailResponse> {
    return apiFetch<SessionDetailResponse>(`/api/sessions/${sessionId}/detail`);
  },
  async delete(sessionId: string): Promise<void> {
    return apiFetch<void>(`/api/sessions/${sessionId}`, {
      method: "DELETE",
    });
  },
};



// ---------------------------------------------------------
// PPT Types & Methods
// ---------------------------------------------------------

export type PptSegmentData = {
  id: string;
  slide_index: number;
  shape_id: string;
  paragraph_index: number;
  run_index: number;
  original_text: string;
  normalized_text: string;
  flags: Array<{
    type: string;
    severity: string;
    explanation?: string;
    matched_text?: string;
    recommendation?: string;
  }>;
  eval_scores: { similarity?: number } | null;
  final_text: string;
  decision: string;
};

export type PptProcessResponse = {
  session: {
    id: string;
    session_type: string;
    input_label: string;
    status: string;
    created_at: string;
    completed_at: string;
  };
  data: {
    total_slides: number;
    total_segments: number;
    slides: Array<{
      slide_index: number;
      slide_number: number;
      segments: PptSegmentData[];
    }>;
  };
};

export type PptSessionDetail = {
  session: SessionDetailResponse["session"];
  output: {
    total_slides: number;
    total_flags: number;
    slides: Record<string, PptSegmentData[]>;
  } | null;
};

export type CompileModification = {
  slide_index: number;
  shape_id: string;
  paragraph_index: number;
  run_index: number;
  new_text: string;
};

export const SettingsAPI = {
  async get(): Promise<any> {
    return apiFetch<any>("/api/settings/");
  },
  async update(data: any): Promise<any> {
    return apiFetch<any>("/api/settings/", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },
};

export const PptAPI = {
  async process(formData: FormData): Promise<PptProcessResponse> {
    return apiFetch<PptProcessResponse>("/api/ppt/process", {
      method: "POST",
      body: formData,
    });
  },
  async batchProcess(formData: FormData): Promise<any[]> {
    return apiFetch<any[]>("/api/ppt/batch-process", {
      method: "POST",
      body: formData,
    });
  },
  async compileSession(
    sessionId: string,
    modifications: CompileModification[]
  ): Promise<Blob> {
    const form = new FormData();
    form.append("modifications", JSON.stringify(modifications));

    return apiFetch<Blob>(`/api/ppt/compile_session/${sessionId}`, {
      method: "POST",
      body: form,
    });
  },
};

export const RewriteAPI = {
  async run(payload: RewriteRequest): Promise<RewriteResponse> {
    return apiFetch<RewriteResponse>("/api/rewrite/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  async rerunSegment(
    sessionId: string,
    segmentId: string,
    tone: TonePreset,
    intensity: RewriteIntensity
  ): Promise<SegmentRewriteResult> {
    return apiFetch<SegmentRewriteResult>(
      `/api/rewrite/segment/${sessionId}/${segmentId}`,
      {
        method: "POST",
        body: JSON.stringify({ tone_preset: tone, intensity }),
      }
    );
  },
};

export const EvalAPI = {
  async score(
    sessionId: string,
    segmentId: string
  ): Promise<{ similarity: number; length_delta: number }> {
    return apiFetch(`/api/eval/score`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, segment_id: segmentId }),
    });
  },
};

export type UserProfile = {
  id: string;
  email: string;
  full_name: string;
  role: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: UserProfile;
};

export const AuthAPI = {
  async signup(data: any): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  async login(data: any): Promise<AuthResponse> {
    return apiFetch<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
  async logout(): Promise<void> {
    await apiFetch<void>("/api/auth/logout", {
      method: "POST",
    });
  },
  async getMe(): Promise<UserProfile> {
    return apiFetch<UserProfile>("/api/auth/me");
  },
};

export type CrashReportPayload = {
  route: string;
  error_type: string;
  message: string;
  stack_summary?: string | null;
  consent_flag: boolean;
  session_id?: string | null;
};

export type TelemetryEvent = {
  id: string;
  timestamp: string;
  user_id: string | null;
  session_id: string | null;
  route: string;
  error_type: string;
  message: string;
  stack_summary: string | null;
  consent_flag: boolean;
};

export type TelemetryListResponse = {
  total: number;
  page: number;
  limit: number;
  events: TelemetryEvent[];
};

export const TelemetryAPI = {
  async recordCrash(payload: CrashReportPayload): Promise<any> {
    return apiFetch<any>("/api/telemetry/crash", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  async getEvents(page = 1, limit = 20): Promise<TelemetryListResponse> {
    return apiFetch<TelemetryListResponse>(`/api/telemetry/events?page=${page}&limit=${limit}`);
  },
};

