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
  id: string;
  requirement: string;
  priority: string;
  confidence: number;
};

export type DocProcessResponse = {
  session: {
    id: string;
    session_type: string;
    input_type: string;
    input_label: string;
    status: string;
    error_message?: string | null;
    created_at: string;
    completed_at: string | null;
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
  async getDetail(sessionId: string): Promise<DocProcessResponse> {
    return apiFetch<DocProcessResponse>(`/api/sessions/${sessionId}/detail`);
  }
};

export const DocAPI = {
  async process(formData: FormData): Promise<DocProcessResponse> {
    return apiFetch<DocProcessResponse>("/api/doc/process", {
      method: "POST",
      body: formData,
    });
  }
};
