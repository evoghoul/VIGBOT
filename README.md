# VIGBOT: Autonomous AI Campus Assistant (VFSTR Vadlamudi)

An autonomous, production-grade AI academic assistant and helpdesk built for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**. Grounded in official institutional bylaws, academic records, attendance percentages, timetable slots, exam schedules, and the **2026-27 Semester-I B.Tech Academic Calendar**.

VIGBOT pairs verified institutional database lookups, 28 verified application capabilities, and security guardrails with **Google Gemini (gemini-3.5-flash)** for natural conversation, **Universal NLU** for zero-false-action intent routing, and a **sub-millisecond CPU-bound Intent Classifier** (TF-IDF Word + Subword Character N-Grams + Multinomial Logistic Regression) for high-speed intent routing and crisis safety.

---

## Key Highlights & Production Status

- **28 Verified Application Capabilities & 48 Operations**: Full bidirectional integration between conversational AI and 28 frontend tabs/routes (Lost & Found, Facility Bookings, Attendance, SGRC Grievance, Student Services, Fee Management, Exams, Hostels, Transport, etc.).
- **Zero False Writes & Zero Fabricated Tickets**: Strict distinction between *asking* and *doing*. Informational inquiries ("where do I report...", "how do I book...") never mutate the database, never fabricate tracking numbers, and provide direct one-click navigation pills.
- **Low-Latency Intent Classification**: Zero-cost, CPU-bound ML intent classifier (~1-2ms on standard CPU) across 18 specialized domain intents with dynamic confidence thresholding and graceful fallback.
- **22+1 Official Languages of India**: Full support for all 22 languages recognized under the 8th Schedule of the Constitution of India plus English, with real-time clickable dropdown and instant search filter.
- **Zero-Delay Mental Health Crisis Guardrail**: Asymmetric safety thresholding for `distress_support` ($\ge 99\%$ recall target) triggering immediate confidential escalation (Tele-MANAS & Crisis Counseling) without ever routing to cloud LLMs.
- **Row-Level Access Control (RLAC) & Prompt Injection Defense**: Hardened security boundaries preventing cross-student record access, unauthorized queries, and prompt injection attempts before model inference.
- **Comprehensive Quality & Test Verification**:
  - **Backend Pytest Suite**: 89 passed, 3 skipped, 1 deselected, 0 failures.
  - **Phase 14 Independent Benchmark**: 252 held-out cases with 0 false writes, 0 fabricated confirmations, and 100% navigation success.
  - **Adversarial Safety Suite**: 15/15 adversarial attack and injection scenarios passing with zero unauthorized mutations.
  - **Frontend E2E Verification**: 28/28 capabilities verified against Next.js components.
  - **Frontend Build**: Next.js 16.3.4 (Turbopack) build succeeded with 0 TypeScript errors.
  - **Scripts Integrity**: 12 standing scripts and 8 archived legacy patches passing with 0 errors.

---

## System Architecture

```
Incoming Student Query
          │
          ▼
[1. Security Guardrail: Prompt Injection & Cross-Student RLAC Defense]
          │ (Passes - not an injection or unauthorized cross-student attempt)
          ▼
[2. Crisis Guardrail: Deterministic Distress Regex Filter]
          │ (Passes - no immediate emergency keywords)
          ▼
[3. Universal NLU & Capability Registry (28 Capabilities, 48 Operations)]
          │ (Strict Safe-Execution Planner: Asks vs Actions vs Navigation)
          ├── Asking/Info/Navigation ─────────► Structured Navigation Action Card (Zero Writes)
          ├── Explicit Action (Submit/Book) ──► Verified Database Tool or Prefill Form Guide
          │
          └── General / Academic Domain Inquiry
                    │
                    ▼
[4. ML Intent Classifier & Semantic RAG Reasoning]
          ├── Confident Match ────────────────► Domain Tool Handler (Attendance, Marks, Schedule)
          └── Deep Pedagogical Inquiry ───────► Offline Local GGUF (8B/1B) or Gemini 3.5 Flash
```

---

## The 18 Target Intents Taxonomy

All target intents are formally declared in [`ml/intents.yaml`](ml/intents.yaml):

| Category | Intents | Description |
| :--- | :--- | :--- |
| **Academic & Student Records** | `attendance`, `exams`, `marks`, `fees`, `timetable`, `curriculum` | Attendance shortage warnings, CIE marks, GPA calculations, dues, weekly timetables, and graduation credit audits. |
| **Campus Facilities & Life** | `facility`, `library`, `hostel`, `transport`, `circulars`, `events`, `clubs`, `services` | Facility bookings, book availability, mess schedules, bus routes, official circulars, and certificates. |
| **Institutional Governance** | `policy_bylaws` | Detentions, condonation policies, academic regulations (R23/R24). |
| **Safety-Critical** | `distress_support` | Crisis intervention, academic panic, helplessness (asymmetric $\tau=0.10$, $\ge 99\%$ recall). |
| **Conversational & Scoping** | `greeting_smalltalk`, `out_of_scope` | Helpdesk onboarding and polite out-of-domain rejection ($\tau=0.50$). |

---

## Prerequisites

Ensure you have installed on your machine:
1. **Python** (v3.10 – v3.12)
2. **Node.js** (v18.0.0 or higher) & **npm** (v9+)
3. *(Optional)* **Google Gemini API Key** (set `GEMINI_API_KEY` in environment for live cloud generative responses)

---

## Quick Start Guide

Clone the repository:
```bash
git clone <your-repository-url>
cd VIGBOT
```

### 1. Start the Backend API (FastAPI)

Open Terminal 1:
```bash
cd BACKEND

# 1. Activate Python virtual environment
# Windows (PowerShell):
..\.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
..\.venv\Scripts\activate.bat
# Linux / macOS:
source ../.venv/bin/activate

# 2. Start the Uvicorn server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs on: `http://localhost:8000` (Interactive Swagger docs available at `http://localhost:8000/docs`).*

### Configuration Options (`BACKEND/app/config.py` or `.env`):
- `USE_INTENT_CLASSIFIER=True|False` (Default: `False` for backward compatibility)
- `DATABASE_URL=sqlite:///../database/vigbot.db`
- `ENABLE_GEMINI=True|False` (Default: `False`)
- `ENABLE_GROQ=False`
- `INTENT_MODEL_PATH=artifacts/intent_model.joblib`
- `INTENT_CONFIG_PATH=artifacts/intent_config.json`

---

### 2. Start the Frontend (Next.js)

Open Terminal 2:
```bash
cd FRONTEND

# 1. Install dependencies
npm install

# 2. Start Next.js development server
npm run dev
```
*Frontend runs on: `http://localhost:3000`.*

---

## Running Verification & Test Suites

The project features a comprehensive test suite covering data guardrails, system endpoints, intent classification, distress safety, and privacy:

```bash
# 1. Run all backend tests:
.\.venv\Scripts\python.exe -m pytest

# 2. Run the 252-case independent real-world evaluation benchmark:
.\.venv\Scripts\python.exe scripts/evaluate_independent_suite.py

# 3. Run the 15-case adversarial action safety suite:
.\.venv\Scripts\python.exe scripts/run_adversarial_safety_suite.py

# 4. Verify frontend E2E capabilities and routes:
.\.venv\Scripts\python.exe scripts/verify_frontend_e2e.py

# 5. Run the standing and archived scripts integrity harness:
.\.venv\Scripts\python.exe scripts/verify_scripts_integrity.py

# 6. Verify frontend production Turbopack build:
npm --prefix FRONTEND run build
```

---

## Demo Student Login Credentials

Log in with pre-seeded student accounts:

| Field | Primary Demo Credential | Alternative Demo Credential |
| :--- | :--- | :--- |
| **Roll Number / Username** | `251FA04E13` | `24CSE001` |
| **Password** | `251FA04E13` (or `student123`) | `student123` |
| **Student Name** | Aman Kumar | Asha Reddy |
| **Branch & Section** | B.Tech CSE (Section 7) | B.Tech CSE (Section A) |

---

## Architectural & Project Documentation

For exhaustive technical references, inspect:
- [`FINAL_PROJECT_STRUCTURE.md`](reports/FINAL_PROJECT_STRUCTURE.md) — Annotated file-by-file directory layout.
- [`PROJECT_CLEANUP_REPORT.md`](reports/PROJECT_CLEANUP_REPORT.md) — Comprehensive 18-section architectural refactoring and optimization report.
- [`PHASE16_FINAL_AUDIT.md`](reports/PHASE16_FINAL_AUDIT.md) — Phase 16 post-cleanup independent audit and runtime verification report.
- [`CLEANUP_FILE_MANIFEST.json`](reports/CLEANUP_FILE_MANIFEST.json) — Inventory of retained, refactored, relocated, and archived files.
- [`CLEANUP_TEST_RESULTS.json`](reports/CLEANUP_TEST_RESULTS.json) — Complete machine-readable test results across all suites.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — Systems design, row-level security, and tool dispatch.
- [`docs/UNIVERSAL_INTENT_ROUTING.md`](docs/UNIVERSAL_INTENT_ROUTING.md) — Detailed capability-operation matrix.

---

## License & Attribution

Developed for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**.
All student records, policies, and calendar entries conform to institutional data protection regulations.
