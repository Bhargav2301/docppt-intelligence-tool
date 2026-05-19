"use client";

import { useEffect, useState } from "react";
import { Settings, Save, Shield, Cpu, Zap, Palette, Loader2, CheckCircle, HelpCircle } from "lucide-react";
import { SettingsAPI } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Privacy & Telemetry states
  const [telemetryConsent, setTelemetryConsent] = useState<string>("denied");

  useEffect(() => {
    fetchSettings();
    // Load local telemetry consent state
    if (typeof window !== "undefined") {
      const consent = localStorage.getItem("docppt_crash_consent");
      setTelemetryConsent(consent || "denied");
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
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (e) {
      console.error(e);
      alert("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleTelemetryToggle = () => {
    const nextConsent = telemetryConsent === "granted" ? "denied" : "granted";
    setTelemetryConsent(nextConsent);
    localStorage.setItem("docppt_crash_consent", nextConsent);
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
      id: "local_cpu",
      name: "Local CPU",
      desc: "Runs T5/DistilBART locally using your system's CPU. Privacy-first, zero configuration, but requires downloading models (~500MB).",
      local: true,
      custom: false,
    },
    {
      id: "local_gpu",
      name: "Local GPU",
      desc: "Runs T5/DistilBART locally using your CUDA-compatible GPU for accelerated processing. Requires GPU setup.",
      local: true,
      custom: false,
    },
    {
      id: "extractive_only",
      name: "Extractive Only",
      desc: "Zero local model download. Uses lightweight rules and regex to extract text and strip artifacts. Highly recommended for low-resource environments.",
      local: false,
      custom: false,
    },
    {
      id: "managed_endpoint",
      name: "Managed Hosted LLM",
      desc: "Uses a pre-configured, self-hosted LLM maintained by the developer; no setup required for you.",
      local: false,
      custom: false,
    },
    {
      id: "user_hosted_endpoint",
      name: "Custom Local/OpenAI Endpoint",
      desc: "Connect to your own Ollama, LM Studio, vLLM, or OpenAI-compatible endpoint. Requires configuring an API URL and Model ID.",
      local: false,
      custom: true,
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
          <button className="w-full text-left px-4 py-2.5 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] transition-colors text-sm">
            Integrations
          </button>
          <button className="w-full text-left px-4 py-2.5 rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] transition-colors text-sm">
            Advanced Dev Tools
          </button>
        </div>

        {/* Content */}
        <div className="md:col-span-2 space-y-6">
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

              {/* Dynamic input showing ONLY for user_hosted_endpoint */}
              {settings.model_mode === "user_hosted_endpoint" && (
                <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 space-y-4 animate-fade-in">
                  <div>
                    <label className="block text-xs font-semibold mb-1 text-blue-400">OpenAI-Compatible Local Endpoint</label>
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
                    <label className="block text-xs font-semibold mb-1 text-blue-400">Model ID Identifier</label>
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

              <div className="pt-2">
                <label className="block text-sm font-medium mb-2">PPT Humanization Sensitivity</label>
                <div className="flex items-center gap-4 p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30">
                  <Shield className={`w-10 h-10 ${
                    settings.ppt_sensitivity === "conservative" ? "text-green-500" : 
                    settings.ppt_sensitivity === "balanced" ? "text-blue-500" : "text-orange-500"
                  }`} />
                  <div className="flex-1">
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="1"
                      value={
                        settings.ppt_sensitivity === "conservative" ? 0 : 
                        settings.ppt_sensitivity === "balanced" ? 1 : 2
                      }
                      onChange={(e) => {
                        const vals = ["conservative", "balanced", "aggressive"];
                        setSettings({ ...settings, ppt_sensitivity: vals[parseInt(e.target.value)] });
                      }}
                      className="w-full accent-[var(--accent)]"
                    />
                    <div className="flex justify-between text-[10px] text-[var(--text-muted)] mt-1 uppercase font-bold tracking-widest">
                      <span>Conservative</span>
                      <span>Balanced</span>
                      <span>Aggressive</span>
                    </div>
                  </div>
                </div>
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
                <div className="text-xs text-[var(--text-muted)] leading-relaxed mt-0.5">Keep original .docx and .pptx files inside cache store directories after summaries build.</div>
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
