const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
  created_at: string;
  completed_at: string | null;
  metrics: {
    word_count?: number;
    summary_ready?: boolean;
    total_slides?: number;
    total_flags?: number;
  };
};

export type RequirementItem = {
  text: string;
  priority: string;
  category: string;
};

export type DocProcessResponse = {
  session: {
    id: string;
    session_type: string;
    input_type: string;
    input_label: string;
    status: string;
    created_at: string;
    completed_at: string;
  };
  output: {
    structured_summary: string;
    product_description: string;
    implementation_requirements: Record<string, RequirementItem[]>;
    word_count: number;
  };
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
  output: {
    structured_summary: string;
    product_description: string;
    implementation_requirements: Record<string, RequirementItem[]>;
    word_count: number;
  } | null;
};

export const SessionAPI = {
  async getRecent(): Promise<RecentSessionItem[]> {
    return apiFetch<RecentSessionItem[]>("/api/sessions/recent");
  },
  async getDetail(sessionId: string): Promise<SessionDetailResponse> {
    return apiFetch<SessionDetailResponse>(`/api/sessions/${sessionId}/detail`);
  },
};

export const DocAPI = {
  async process(formData: FormData): Promise<DocProcessResponse> {
    return apiFetch<DocProcessResponse>("/api/doc/process", {
      method: "POST",
      body: formData,
    });
  }
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

export const PptAPI = {
  async process(formData: FormData): Promise<PptProcessResponse> {
    return apiFetch<PptProcessResponse>("/api/ppt/process", {
      method: "POST",
      body: formData,
    });
  },
  async compileSession(
    sessionId: string,
    modifications: CompileModification[]
  ): Promise<Blob> {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const form = new FormData();
    form.append("modifications", JSON.stringify(modifications));

    const res = await fetch(`${API_BASE}/api/ppt/compile_session/${sessionId}`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, err.detail || "Compilation failed");
    }

    return res.blob();
  },
};

