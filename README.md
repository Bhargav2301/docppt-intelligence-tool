# 📄 DocPPT Intelligence Tool

> **Convert client requirement documents into structured product specifications and clean AI-looking slide text into natural, presentation-ready language.**

---

## 🚀 Overview

The **DocPPT Intelligence Tool** is a web-based document intelligence and PowerPoint humanization platform. It solves a common pain point for product development consultants, founders, product managers, and freelance builders who receive client requirements in messy Google Docs or AI-assisted presentation decks.

By leveraging **free, local, and small-model NLP pipelines** (rather than relying strictly on paid external LLM APIs), the MVP processes text locally, runs quality checks, flags citation residues/artifacts, and rewrites text for presentation-ready outcomes while preserving slide structure and intent.

---

## 🛠️ Key Features

### 1. Google Docs & Text Spec Generation
* **Document Parser:** Extract headers, hierarchy, lists, and paragraphs from uploaded `.docx` files, Google Doc URLs, or raw text.
* **Local Summarization:** Uses a hybrid pipeline (extractive ranking like LexRank/TextRank and local small abstractive models like DistilBART or Flan-T5) to summarize documents.
* **Spec Generator:** Inferred product descriptions, target users, core benefit statements, and primary user workflows.
* **Requirements Extractor:** Automatically groups requirements into Functional, Technical, Integrations, Data, UI/UX, and Security/Privacy categories.

### 2. PowerPoint (PPTX) Humanizer
* **Text Extractor:** Extracts text slide-by-slide and shape-by-shape, keeping track of slide IDs and text runs.
* **Artifact Detection:** Flags citation brackets (e.g., `[1]`, `[Source]`), delimiters, smart-character residue, and markdown markers.
* **AI-Likeness Analyzer:** Computes readability and text style metrics (sentence burstiness, lexical variety, POS patterns, n-gram repetitions) as quality signals.
* **Humanization Rewrite:** Rewrites flagged segments to sound natural, concise, and professional while retaining original factual intent.
* **Layout-Safe Export:** Re-compiles the `.pptx` deck with modified text runs, ensuring 100% fidelity for non-text assets (images, shapes, tables, charts, slide count).

---

## 📂 Repository Structure

The project is organized as a monorepo containing the following components:

```
docppt-intelligence-tool/
├── apps/
│   └── web/                   # Next.js frontend (React 19, TypeScript, Tailwind CSS v4)
├── services/
│   └── nlp/                   # FastAPI backend service (Python, SQLAlchemy, SQLite/PostgreSQL)
├── packages/
│   └── shared/                # Shared monorepo packages (for future components)
├── docs/                      # Architectural designs, PRD, TRD, and deployment guides
├── render.yaml                # Infrastructure-as-code Blueprint for Render deployments
└── README.md                  # Root documentation
```

---

## ⚡ Getting Started

### 📋 Prerequisites
* **Frontend:** [Node.js v20+](https://nodejs.org/) & `npm`
* **Backend:** [Python 3.10+](https://www.python.org/) & `pip`
* **Database:** SQLite (local development default) or PostgreSQL (production)

---

### 🔧 1. Backend Setup (`services/nlp`)

Navigate to the NLP service directory:
```bash
cd services/nlp
```

#### Step 1.1: Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 1.2: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 1.3: Run the Development Server
```bash
uvicorn main:app --reload --port 8000
```
The FastAPI documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

> [!NOTE]
> During development startup, the server automatically runs database migrations and seeds a default developer user if none exists:
> - **Username:** `local_user@example.com`
> - **Password:** `password`

---

### 💻 2. Frontend Setup (`apps/web`)

Navigate to the frontend directory:
```bash
cd apps/web
```

#### Step 2.1: Install Node Dependencies
```bash
npm install
```

#### Step 2.2: Configure Environment Variables
Create a `.env.local` file:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### Step 2.3: Run the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to view the application.

---

## 🔌 API Reference Summary

The FastAPI backend exposes the following routers (configured under `services/nlp/main.py`):

| Router / Path | Purpose | Key Functionality |
| :--- | :--- | :--- |
| `/auth` | Authentication | Login, Registration, JWT issuing |
| `/sessions` | Session Management | Save and recall user processing sessions |
| `/models` | Model Status | Get status of local and loaded SLM pipelines |
| `/doc` | Document Parsing | Extract text from uploaded documents |
| `/analysis` | Spec Generation | Generate summaries and specs from parsed text |
| `/ppt` | PPT Parsing & Export | Process PPTX uploads and output clean presentations |
| `/ppt_analysis` | Slide Inspection | Detect citation/AI-likeness artifacts in slides |
| `/eval` | Spec Evaluation | Validate and score generated requirements |
| `/rewrite` | Text Humanization | Propose natural language rewrites for slide items |
| `/settings` | User Settings | Manage custom tones, local endpoints, and presets |
| `/export` | Format Exporter | Download requirements as Markdown or JSON |
| `/telemetry` | Telemetry Logs | Track pipeline success rates and performance metrics |
| `/health` | Health Check | Basic API heartbeat check |

---

## 🌐 Production Deployment

The project is configured for single-click deployment to **Render** using the [render.yaml](file:///c:/Projects/Samtool/docppt-intelligence-tool/render.yaml) blueprint file.

### Services Spawned:
1. **`docppt-backend`** (Web Service): A Docker-based container running the FastAPI server.
2. **`docppt-frontend`** (Web Service): A Docker-based Next.js build.
3. **`docppt-db`** (PostgreSQL Database): Free tier managed Postgres instance.

### Automatic Build Arguments:
Render automatically injects the service's `envVars` as Docker build arguments. This ensures `NEXT_PUBLIC_API_BASE_URL` is baked into the Next.js static asset build phase without separate complex arguments.

To deploy, simply link your fork/repository to Render under the Blueprints page.