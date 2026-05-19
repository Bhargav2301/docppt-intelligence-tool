# Advanced AI Models Support

## Overview
Extend the tool to support high-quality local models like Llama 3 or Mistral via user-hosted endpoints.

## Supported Model Modes
- `localcpu`: Existing small models (T5, GPT2).
- `localgpu`: Existing small models with GPU acceleration.
- `userhostedendpoint`: Connects to an external OpenAI-compatible API (e.g., Ollama, LocalAI, vLLM).

## Configuration
Users can configure these in the **Settings** page:
- **Advanced AI Enabled**: Toggle.
- **Endpoint URL**: `http://localhost:11434/v1` (Ollama default).
- **Model Name**: `llama3`, `mistral`, etc.

## Fallback Logic
If the advanced model endpoint is unreachable or returns an error:
1. Log the failure in `model_runs`.
2. Fall back to the default `localcpu` model (e.g., `flan-t5-small`).
3. Notify the user via a "Quality Degradation" warning in the UI.

## Resource Requirements
- **Small Models**: 2-4GB RAM.
- **Advanced Models**: 8GB+ VRAM (GPU) or 16GB+ RAM (CPU/GGUF).
- Users are responsible for hosting the advanced model endpoint.
