# VIGBOT: Autonomous AI Campus Assistant (VFSTR Vadlamudi)

An autonomous AI assistant built for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**. Grounded in official institutional bylaws, academic records, attendance percentages, timetable slots, exam schedules, and the **2026-27 Semester-I B.Tech Academic Calendar**.

VIGBOT pairs verified institutional database lookups and security guardrails with **Google Gemini (gemini-3.5-flash)** for natural conversation and a **sub-millisecond CPU-bound Intent Classifier** (TF-IDF Word + Subword Character N-Grams + Multinomial Logistic Regression) for zero-cost, high-speed intent routing and crisis safety.

---

## Key Features

- **Low-Latency Intent Classification**: Zero-cost, CPU-bound ML intent classifier (~1-2ms on standard CPU) across 18 specialized domain intents with dynamic confidence thresholding and graceful fallback to Gemini.
- **22+1 Official Languages of India**: Full support for all 22 languages recognized under the 8th Schedule of the Constitution of India plus English, with real-time clickable dropdown and instant search filter.
- **Zero-Delay Mental Health Crisis Guardrail**: Asymmetric safety thresholding for `distress_support` ($\ge 99\%$ recall target) triggering immediate confidential escalation (Tele-MANAS & Crisis Counseling) without ever routing to cloud LLMs.
- **Row-Level Access Control (RLAC) & Prompt Injection Defense**: Hardened security boundaries preventing cross-student record access, unauthorized queries, and prompt injection attempts before model inference.
- **Traceable Telemetry (`routed_by`)**: Full observability over how every answer is generated (`rules`, `classifier`, `gemini`, `classifier_pipeline_test`).
- **Official VFSTR Academic Calendar (2026-27)**: Grounded in the official B.Tech 2nd (R25), 3rd (R22C24) & 4th (R22) Year academic calendar (Dated: 6/1/2026).
- **Interactive Voice Input**: Speech-to-text microphone with live visual waveform audio meter.
- **Privacy-First Zero-PII Logging**: Classifier logs operational telemetry (intent, confidence, threshold) but never stores or logs student query text.

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
[3. ML Intent Classifier Service] (Controlled by USE_INTENT_CLASSIFIER)
   - Token & Subword Char Feature Extraction
   - Logistic Regression Inference (~1-2ms CPU inference)
   - Intent-Specific Confidence Threshold Evaluation
          ├── Confident (>= Threshold) ───────► Direct Service Handler (routed_by="classifier")
          │                                      [attendance, exams, fees, timetable, etc.]
          │                                      * If distress_support: Immediate Crisis Escalation
          │
          └── Unconfident (< Threshold) ──────► Seamless Graceful Fallback
                                                 │
                                                 ├── Deterministic Rules (routed_by="rules")
                                                 └── Cloud Gemini 2.5 Flash (routed_by="gemini")
```

---

## The 18 Target Intents Taxonomy

All target intents are formally declared in [`ml/intents.yaml`](ml/intents.yaml):

| Category | Intents | Description |
| :--- | :--- | :--- |
| **Academic & Student Records** | `attendance`, `exams`, `marks`, `fees`, `timetable`, `curriculum` | Attendance shortage warnings, CIE marks, GPA calculations, dues, weekly timetables, and graduation credit audits. |
| **Campus Facilities & Life** | `faculty`, `library`, `hostel`, `transport`, `circulars`, `events`, `clubs`, `services` | Faculty cabin contacts, book availability, mess schedules, bus routes, official circulars, and certificates. |
| **Institutional Governance** | `policy_bylaws` | Detentions, condonation policies, academic regulations (R23/R24). |
| **Safety-Critical** | `distress_support` | Crisis intervention, academic panic, helplessness (asymmetric $\tau=0.10$, $\ge 99\%$ recall). |
| **Conversational & Scoping** | `greeting_smalltalk`, `out_of_scope` | Helpdesk onboarding and polite out-of-domain rejection ($\tau=0.50$). |

---

## Machine Learning Pipeline & Data Governance

### 1. Author Sequestration & Leakage Prevention
To evaluate true out-of-distribution generalization across writing styles:
- **Training Authors**: `aman`, `pragna`, `sirisha` (in [`data/authors/`](data/authors/)).
- **Starter Foundation**: `agent` (in [`data/intents.csv`](data/intents.csv)).
- **Dedicated Quarantined Test Author**: `sridhar` (`sridhar.csv`). Never included in training or hyperparameter tuning.
- **Fuzzy Contamination Checks**: [`data/validate_data.py`](data/validate_data.py) runs Token Jaccard and Character Difflib similarity across all test and training rows, flagging pairs $> 0.80$ to eliminate leakage.

### 2. Validation & Quality Checks
Run dataset validation with strict exit codes:
```bash
python data/validate_data.py --strict
```

### 3. Model Training & Cross-Validation
Train the classifier using Leave-One-Author-Out (LOAO) cross-validation:
```bash
# Production training (requires completed human author quotas):
python ml/train_intent.py

# Preliminary / Dry-run training:
python ml/train_intent.py --allow-partial
```

### 4. Threshold Sweep & Optimization
Tune asymmetric confidence thresholds:
```bash
python ml/tune_threshold.py --allow-partial
```

### 5. Benchmark Evaluation
Evaluate rules, trained classifier, and Gemini 2.5 Flash on the identical question subset:
```bash
python ml/evaluate_intent.py --allow-partial
```

> Detailed documentation on mathematical formulations, calibration caveats (ECE), and viva defense preparation is available in [`docs/INTENT_MODEL_EXPLAINED.md`](docs/INTENT_MODEL_EXPLAINED.md).

---

## Prerequisites

Ensure you have installed on your machine:
1. **Python** (v3.10 – v3.12)
2. **Node.js** (v18.0.0 or higher) & **npm** (v9+)
3. *(Optional)* **Google Gemini API Key** (set `GEMINI_API_KEY` in environment for live generative responses)

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

# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Uvicorn server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend runs on: `http://localhost:8000` (Interactive Swagger docs available at `http://localhost:8000/docs`).*

### Configuration Options (`BACKEND/app/config.py` or `.env`):
- `USE_INTENT_CLASSIFIER=True|False` (Default: `False` for backward compatibility)
- `ALLOW_PIPELINE_TEST_MODEL=True|False` (Default: `False` — prevents loading test models in production)
- `INTENT_MODEL_PATH=artifacts/intent_model.joblib`
- `INTENT_CONFIG_PATH=artifacts/intent_config.json`
- `GEMINI_API_KEY=<your-gemini-key>`
- `GEMINI_MODEL=gemini-3.5-flash`

---

### 2. Start the Frontend (Next.js)

Open Terminal 2:
```bash
cd FRONTEND

# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```
*Frontend runs on: `http://localhost:3000`.*

---

## Running the Automated Test Suites

The project features a comprehensive test suite covering data guardrails, system endpoints, intent classification, distress safety, and privacy:

```bash
# Run all tests across the repository:
pytest -v

# Run backend unit and integration tests:
pytest BACKEND/tests/ -v

# Run data guardrails and leakage prevention tests:
pytest tests/test_data_guardrails.py -v
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

## Project Structure

```
VIGBOT/
├── BACKEND/                     # FastAPI Backend Application
│   ├── app/
│   │   ├── agent/               # Orchestrator, NLU Engine, Intent Classifier & LLM Client
│   │   │   ├── intent_classifier.py  # IntentClassifierService with safety guardrails
│   │   │   ├── nlu_engine.py         # Rule routing, prompt injection defense & crisis checks
│   │   │   ├── orchestrator.py       # Conversational orchestrator & context tracking
│   │   │   └── llm_client.py         # Google Gemini & Groq fallback client
│   │   ├── api/                 # Auth, Conversations, Service Requests endpoints
│   │   ├── database.py          # SQLite data repository with Row-Level Access Control
│   │   ├── models/schemas.py    # Pydantic schemas (including routed_by in MessageResponse)
│   │   └── config.py            # Environment settings and feature flags
│   ├── tests/                   # Backend PyTest test suite (test_vigbot, test_intent_classifier)
│   └── requirements.txt         # Backend Python dependencies
├── FRONTEND/                    # Next.js (React + Tailwind CSS) Frontend
│   └── src/
│       ├── components/          # Header, Sidebar, AI Chat Panel, Calendar, Exams, Timetable
│       ├── context/             # StudentContext, AgentChatContext, LanguageContext
│       └── lib/                 # api-client.ts, translations, auth logic
├── data/                        # Dataset Governance & Author Split Repository
│   ├── authors/                 # Teammate CSV files (aman.csv, pragna.csv, sirisha.csv, sridhar.csv)
│   ├── intents.csv              # Agent starter baseline rows
│   ├── validate_data.py         # Strict encoding, duplicate, quota & leakage validator
│   └── README.md                # Data collection guidelines and rules
├── ml/                          # Machine Learning Pipeline & Evaluation
│   ├── intents.yaml             # Complete 18-intent formal taxonomy declaration
│   ├── train_intent.py          # TF-IDF + Logistic Regression LOAO trainer
│   ├── tune_threshold.py        # Asymmetric threshold sweep & optimization
│   ├── evaluate_intent.py       # Comparative benchmarking (Rules vs Classifier vs Gemini)
│   └── requirements.txt         # ML tooling dependencies
├── docs/                        # Technical Documentation & Viva Guides
│   ├── INTENT_MODEL_EXPLAINED.md# Comprehensive architecture, math, safety & viva Q&A
│   └── intent_classifier_plan.md# Initial engineering specification and approval artifact
├── tests/                       # Root-level test suites
│   └── test_data_guardrails.py  # Tests for strict data validation & leakage prevention
├── database/
│   └── vigbot.db      # Pre-seeded SQLite database (315 students, marks, fees, timetable)
├── pytest.ini                   # PyTest configuration
└── README.md                    # Project overview & documentation (this file)
```

---

## License & Attribution

Developed for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**.
All student records, policies, and calendar entries conform to institutional data protection regulations.
