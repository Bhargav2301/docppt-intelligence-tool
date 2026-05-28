/* eslint-disable */
"use client";

import { useEffect, useState } from "react";
import { Settings, Save, Shield, Cpu, Zap, Loader2, CheckCircle, Key, RefreshCw, AlertCircle, Database } from "lucide-react";
import { SettingsAPI, apiFetch } from "@/lib/api";

const TONE_PRESETS = [
  { value: "presentation_concise", label: "Concise" },
  { value: "executive_polished", label: "Executive" },
  { value: "founder_clear", label: "Founder" },
  { value: "product_manager_direct", label: "Product" },
  { value: "consulting_professional", label: "Consulting" },
];

const INTENSITIES = [
  { value: "minimal", label: "Minimal" },
  { value: "balanced", label: "Balanced" },
  { value: "strong", label: "Strong" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Gemini API Key state (kept strictly local / in-session)
  const [geminiApiKey, setGeminiApiKey] = useState("");
  
  // Privacy & Telemetry states
  const [telemetryConsent, setTelemetryConsent] = useState<string>("denied");

  // Test states
  const [testingGemini, setTestingGemini] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState<{ status: "success" | "error"; message: string } | null>(null);
  
  const [testingLocal, setTestingLocal] = useState(false);
  const [localTestResult, setLocalTestResult] = useState<{ status: "success" | "error" | "not_running"; message: string } | null>(null);

  useEffect(() => {
    fetchSettings();
    // Load local states from browser storage
    if (typeof window !== "undefined") {
      const consent = localStorage.getItem("docppt_crash_consent");
      setTelemetryConsent(consent || "denied");
      
      const storedKey = sessionStorage.getItem("gemini_api_key");
      setGeminiApiKey(storedKey || "");
    }
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await SettingsAPI.get();
      setSettings(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      await SettingsAPI.update({
        model_mode: settings.model_mode,
        ppt_sensitivity: settings.ppt_sensitivity,
        theme: settings.theme,
        retain_source_files: settings.retain_source_files,
        advanced_instruction_model: settings.advanced_instruction_model || "llama3",
        advanced_model_endpoint: settings.advanced_model_endpoint || "http://localhost:11434/v1",
        default_tone_preset: settings.default_tone_preset || "presentation_concise",
        default_intensity: settings.default_intensity || "balanced",
        local_model_endpoint: settings.local_model_endpoint || "http://localhost:11434",
      });
      
      // Save Gemini key to sessionStorage strictly
      if (typeof window !== "undefined") {
        if (geminiApiKey.trim()) {
          sessionStorage.setItem("gemini_api_key", geminiApiKey.trim());
        } else {
          sessionStorage.removeItem("gemini_api_key");
        }
      }
      
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error(e);
      alert("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const testGeminiConnection = async () => {
    if (!geminiApiKey.trim()) {
      setGeminiTestResult({ status: "error", message: "Please enter a Gemini API Key first." });
      return;
    }
    
    // Temporarily set it in session storage so apiFetch can read and send it encrypted
    const oldKey = sessionStorage.getItem("gemini_api_key");
    sessionStorage.setItem("gemini_api_key", geminiApiKey.trim());

    setTestingGemini(true);
    setGeminiTestResult(null);
    try {
      const res = await apiFetch<{ status: string; message: string }>("/api/settings/test-gemini");
      setGeminiTestResult({ status: "success", message: res.message || "Gemini connection successful!" });
    } catch (err: any) {
      setGeminiTestResult({ status: "error", message: err.message || "Failed to connect to Gemini." });
      // Revert if connection failed and there was no previous key
      if (!oldKey) {
        sessionStorage.removeItem("gemini_api_key");
      }
    } finally {
      setTestingGemini(false);
      // Restore old key if we only wanted to test
      if (oldKey) {
        sessionStorage.setItem("gemini_api_key", oldKey);
      }
    }
  };

  const testLocalModelConnection = async () => {
    const url = settings.local_model_endpoint || "http://localhost:11434";
    setTestingLocal(true);
    setLocalTestResult(null);
    try {
      const res = await apiFetch<{ status: "success" | "not_running" | "error"; message: string }>(`/api/settings/test-local-model?url=${encodeURIComponent(url)}`);
      setLocalTestResult({ status: res.status, message: res.message || "Successfully connected to local model server!" });
    } catch (err: any) {
      setLocalTestResult({ status: "error", message: err.message || "Failed to connect to local model server." });
    } finally {
      setTestingLocal(false);
    }
  };

  const handleTelemetryToggle = () => {
    const nextConsent = telemetryConsent === "granted" ? "denied" : "granted";
    setTelemetryConsent(nextConsent);
    localStorage.setItem("docppt_crash_consent", nextConsent);
  };

  const handleClearKey = () => {
    setGeminiApiKey("");
    sessionStorage.removeItem("gemini_api_key");
    setGeminiTestResult(null);
  };

  if (!settings) {
    return (
      <div className="flex justify-center items-center h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
      </div>
    );
  }

  const modelModes = [
    {
      id: "gemini_byok",
      name: "Gemini BYOK (Bring Your Own Key)",
      desc: "Uses Google's Gemini LLM. The API key is stored only in your browser's session storage and sent encrypted in transit. Privacy-first, high quality rewrites.",
    },
    {
      id: "local_cpu",
      name: "Local CPU",
      desc: "Runs T5/DistilBART locally using your system's CPU. Privacy-first, zero configuration, but requires downloading models (~500MB).",
    },
    {
      id: "local_gpu",
      name: "Local GPU",
      desc: "Runs T5/DistilBART locally using your CUDA-compatible GPU for accelerated processing. Requires GPU setup.",
    },
    {
      id: "extractive_only",
      name: "Extractive Only",
      desc: "Zero local model download. Uses lightweight rules and regex to extract text and strip artifacts. Highly recommended for low-resource environments.",
    },
    {
      id: "managed_endpoint",
      name: "Managed Hosted LLM",
      desc: "Uses a pre-configured, self-hosted LLM maintained by the developer; no setup required for you.",
    },
    {
      id: "user_hosted_endpoint",
      name: "Custom Local/OpenAI Endpoint",
      desc: "Connect to your own Ollama, LM Studio, vLLM, or OpenAI-compatible endpoint. Requires configuring an API URL and Model ID.",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12 animate-fade-in">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-[var(--text-secondary)] mt-1">Configure your AI preferences and workspace.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-2.5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-lg font-semibold transition-all shadow-lg shadow-[var(--accent)]/20 disabled:opacity-50"
        >
          {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : saveSuccess ? <CheckCircle className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saveSuccess ? "Saved!" : "Save Changes"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Sidebar Navigation */}
        <div className="space-y-1">
          <button className="w-full text-left px-4 py-2.5 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] font-medium text-sm">
            General Options
          </button>
        </div>

        {/* Content */}
        <div className="md:col-span-2 space-y-6">
          {/* Rewrite Preferences Section */}
          <section className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-6">
            <div className="flex items-center gap-2 text-lg font-bold text-[var(--text-primary)]">
              <Zap className="w-5 h-5 text-[var(--accent)]" />
              Rewrite Preferences
            </div>

            <div className="space-y-4">
              {/* Default Tone Preset */}
              <div>
                <label className="block text-sm font-medium mb-1.5">Default Tone Preset</label>
                <select
                  value={settings.default_tone_preset || "presentation_concise"}
                  onChange={(e) => setSettings({ ...settings, default_tone_preset: e.target.value })}
                  className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] font-medium"
                >
                  {TONE_PRESETS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Default Intensity */}
              <div>
                <label className="block text-sm font-medium mb-1.5">Default Intensity</label>
                <div className="grid grid-cols-3 gap-2 bg-[var(--bg-elevated)]/40 p-1 rounded-lg border border-[var(--border-subtle)]">
                  {INTENSITIES.map((intensity) => (
                    <button
                      key={intensity.value}
                      type="button"
                      onClick={() => setSettings({ ...settings, default_intensity: intensity.value })}
                      className={`py-1.5 text-xs font-semibold rounded-md transition-all ${
                        settings.default_intensity === intensity.value
                          ? "bg-[var(--accent)] text-white shadow-sm"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      }`}
                    >
                      {intensity.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* AI Configuration Section */}
          <section className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-6">
            <div className="flex items-center gap-2 text-lg font-bold text-[var(--text-primary)]">
              <Cpu className="w-5 h-5 text-[var(--accent)]" />
              AI Mode Selection
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-3">Model Execution Mode</label>
                <div className="space-y-3">
                  {modelModes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      onClick={() => setSettings({ ...settings, model_mode: mode.id })}
                      className={`w-full p-4 rounded-xl border text-left transition-all flex flex-col gap-1 ${
                        settings.model_mode === mode.id
                          ? "border-[var(--accent)] bg-[var(--accent)]/5 ring-1 ring-[var(--accent)]"
                          : "border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30 hover:border-[var(--border-strong)]"
                      }`}
                    >
                      <div className="flex items-center justify-between w-full">
                        <span className="font-semibold text-sm text-[var(--text-primary)]">{mode.name}</span>
                        {settings.model_mode === mode.id && (
                          <span className="w-2 h-2 rounded-full bg-[var(--accent)]" />
                        )}
                      </div>
                      <div className="text-xs text-[var(--text-secondary)] leading-relaxed mt-0.5">
                        {mode.desc}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic input showing ONLY for gemini_byok */}
              {settings.model_mode === "gemini_byok" && (
                <div className="p-4 rounded-xl border border-purple-500/20 bg-purple-500/5 space-y-4 animate-fade-in">
                  <div>
                    <label className="flex items-center justify-between text-xs font-semibold mb-1.5 text-purple-400">
                      <span className="flex items-center gap-1.5">
                        <Key className="w-3.5 h-3.5" /> Gemini API Key (BYOK)
                      </span>
                      {geminiApiKey && (
                        <button
                          type="button"
                          onClick={handleClearKey}
                          className="text-[10px] text-red-400 hover:underline font-bold"
                        >
                          Clear key
                        </button>
                      )}
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="password"
                        placeholder="AIzaSy..."
                        value={geminiApiKey}
                        onChange={(e) => setGeminiApiKey(e.target.value)}
                        className="flex-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-400"
                      />
                      <button
                        type="button"
                        onClick={testGeminiConnection}
                        disabled={testingGemini || !geminiApiKey.trim()}
                        className="px-3 py-2 text-xs font-semibold rounded bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
                      >
                        {testingGemini ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                        Test
                      </button>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)] mt-1.5 block">
                      Key is stored in session only — cleared on tab close. It is transmitted encrypted with the backend's RSA public key.
                    </span>

                    {/* Gemini Connection Test Result */}
                    {geminiTestResult && (
                      <div className={`mt-2 p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
                        geminiTestResult.status === "success" 
                          ? "bg-green-500/5 text-green-400 border-green-500/10" 
                          : "bg-red-500/5 text-red-400 border-red-500/10"
                      }`}>
                        {geminiTestResult.status === "success" ? <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />}
                        <span>{geminiTestResult.message}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Dynamic input showing ONLY for user_hosted_endpoint */}
              {settings.model_mode === "user_hosted_endpoint" && (
                <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 space-y-4 animate-fade-in">
                  <div>
                    <label className="block text-xs font-semibold mb-1.5 text-blue-400">OpenAI-Compatible Local Endpoint</label>
                    <input
                      type="url"
                      placeholder="http://localhost:11434/v1"
                      value={settings.advanced_model_endpoint || ""}
                      onChange={(e) => setSettings({ ...settings, advanced_model_endpoint: e.target.value })}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
                    />
                    <span className="text-[10px] text-[var(--text-muted)] mt-1 block">Default Ollama: http://localhost:11434/v1 | LM Studio: http://localhost:1234/v1</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold mb-1.5 text-blue-400">Model ID Identifier</label>
                    <input
                      type="text"
                      placeholder="llama3:latest"
                      value={settings.advanced_instruction_model || ""}
                      onChange={(e) => setSettings({ ...settings, advanced_instruction_model: e.target.value })}
                      className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-md px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
                    />
                    <span className="text-[10px] text-[var(--text-muted)] mt-1 block">Enter local model tag (e.g. llama3, mistral, llama3:8b)</span>
                  </div>
                </div>
              )}

              {/* Local Model Endpoint Field */}
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium mb-1.5">
                  <Database className="w-4 h-4 text-[var(--text-secondary)]" /> Local Model Endpoint URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    placeholder="http://localhost:11434"
                    value={settings.local_model_endpoint || ""}
                    onChange={(e) => setSettings({ ...settings, local_model_endpoint: e.target.value })}
                    className="flex-1 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]"
                  />
                  <button
                    type="button"
                    onClick={testLocalModelConnection}
                    disabled={testingLocal}
                    className="px-4 py-2 text-sm font-semibold rounded-lg bg-blue-500/10 text-blue-300 border border-blue-500/20 hover:bg-blue-500/20 transition-all flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {testingLocal ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Test Connection
                  </button>
                </div>
                <span className="text-[10px] text-[var(--text-muted)] mt-1.5 block">
                  The URL of your self-hosted Ollama or LM Studio instance. Default Ollama is http://localhost:11434.
                </span>

                {/* Local Model Connection Test Result */}
                {localTestResult && (
                  <div className={`mt-2 p-2.5 rounded-lg border text-xs flex items-start gap-2 ${
                    localTestResult.status === "success" 
                      ? "bg-green-500/5 text-green-400 border-green-500/10" 
                      : localTestResult.status === "not_running"
                      ? "bg-amber-500/5 text-amber-400 border-amber-500/10"
                      : "bg-red-500/5 text-red-400 border-red-500/10"
                  }`}>
                    {localTestResult.status === "success" ? (
                      <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    ) : (
                      <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    )}
                    <span>
                      {localTestResult.status === "not_running"
                        ? "No server found at this address. Make sure Ollama or LM Studio is running locally."
                        : localTestResult.message}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* Privacy & Telemetry Section */}
          <section className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-6">
            <div className="flex items-center gap-2 text-lg font-bold text-[var(--text-primary)]">
              <Shield className="w-5 h-5 text-[var(--accent)]" />
              Privacy & Crash Reports
            </div>
            
            <div className="flex items-center justify-between p-4 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]">
              <div className="pr-4">
                <div className="font-semibold text-sm text-[var(--text-primary)]">Allow Crash Telemetry</div>
                <div className="text-xs text-[var(--text-muted)] leading-relaxed mt-0.5">
                  Automatically share anonymous crash reports to help developers trace and fix bugs. Reports never contain document text.
                </div>
              </div>
              <button
                type="button"
                onClick={handleTelemetryToggle}
                className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${
                  telemetryConsent === "granted" ? "bg-[var(--accent)]" : "bg-gray-600"
                }`}
              >
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${
                  telemetryConsent === "granted" ? "left-7" : "left-1"
                }`} />
              </button>
            </div>
          </section>

          {/* Performance Section */}
          <section className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-6">
            <div className="flex items-center gap-2 text-lg font-bold text-[var(--text-primary)]">
              <Zap className="w-5 h-5 text-[var(--accent)]" />
              Workspace Cache
            </div>
            
            <div className="flex items-center justify-between p-4 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]">
              <div>
                <div className="font-semibold text-sm text-[var(--text-primary)]">Retain Source Decks & Documents</div>
                <div className="text-xs text-[var(--text-muted)] leading-relaxed mt-0.5">Keep original .pptx files inside cache store directories after summaries build.</div>
              </div>
              <button
                type="button"
                onClick={() => setSettings({ ...settings, retain_source_files: !settings.retain_source_files })}
                className={`w-12 h-6 rounded-full transition-colors relative flex-shrink-0 ${
                  settings.retain_source_files ? "bg-[var(--accent)]" : "bg-gray-600"
                }`}
              >
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${
                  settings.retain_source_files ? "left-7" : "left-1"
                }`} />
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
