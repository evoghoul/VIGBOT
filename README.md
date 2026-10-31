# VIGBOT: Autonomous AI Campus Assistant (VFSTR Vadlamudi)

An autonomous, production-grade AI academic assistant and helpdesk built for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**. Grounded in official institutional bylaws, academic records, attendance percentages, timetable slots, exam schedules, and the **2026-27 Semester-I B.Tech Academic Calendar**.

VIGBOT pairs verified institutional database lookups, 28 verified application capabilities, and security guardrails with a **23-Tool Knowledge Graph Registry**, an algorithmic **Dijkstra Campus Navigation Graph**, and a **sub-millisecond CPU-bound Intent Classifier** (TF-IDF Word + Subword Character N-Grams + Multinomial Logistic Regression) for high-speed intent routing and crisis safety.

---

## 🌐 Live Production Deployment

VIGBOT is fully deployed and operational across cloud infrastructure:

| Component | Platform | Live URL / Identifier | Status |
| :--- | :--- | :--- | :---: |
| **Frontend Web App** | Vercel (Next.js 16 Turbopack) | **[student-helpdesk-agent-five.vercel.app](https://student-helpdesk-agent-five.vercel.app)** | **LIVE** |
| **Backend API** | Render (FastAPI Docker) | **[vigbot-api.onrender.com](https://vigbot-api.onrender.com)** | **LIVE** |
| **Database** | Neon (Lakebase Postgres) | `vigbot-db` (Branch: `production`) | **LIVE** |
| **Interactive API Docs** | Swagger UI (FastAPI) | **[vigbot-api.onrender.com/docs](https://vigbot-api.onrender.com/docs)** | **LIVE** |

---

## Key Highlights & Production Status

- **Live Cloud Database on Neon Lakebase Postgres**: Decoupled serverless storage running on AWS US East (Ohio), fully seeded with 315 students, 22 faculty, 977 attendance logs, 2,922 marks records, 4,944 timetable slots, and institutional knowledge tables.
- **Answer-First Rule & 23-Tool Registry**: Every factual query provides a direct, verifiable answer in the first sentence with structured data badges and source citations.
- **Campus Spatial Directory & Dijkstra Navigation Graph**: Algorithmic pathfinding across 23 campus nodes and 18 directed edges from Main Gate (Node 0) to Convocation Hall, NTR Library, MHP Canteen, Chest Supermarket, E-Block, and U-Block.
- **Module-Grounded Truth**:
  - **Central Library**: Open Sundays from 09:00 AM to 05:00 PM (09:00 - 17:00) for reading rooms and digital study spaces.
  - **Hostel Mess Facilities**: Decentralized internal dining halls located on the ground floor of each individual hostel building.
  - **Hostel Bus Shuttles**: Verified morning (07:45 AM - 11:35 AM) and evening return (01:45 PM - 09:00 PM) schedules for KM, Villas SP, and AP/AR/AA/AO routes.
  - **Lost Student ID Replacement**: Authoritative 2-phase state machine (Phase 1: Digital report on sidebar board $\to$ Phase 2: Administrative replacement in H-Block Ground Floor Room H-G04, ₹100 challan, 2-day turnaround).
- **28 Verified Application Capabilities & 48 Operations**: Full bidirectional integration between conversational AI and 28 frontend tabs/routes (Lost & Found, Facility Bookings, Attendance, SGRC Grievance, Student Services, Fee Management, Exams, Hostels, Transport, etc.).
- **Zero False Writes & Zero Fabricated Tickets**: Strict distinction between *asking* and *doing*. Informational inquiries ("where do I report...", "how do I book...") never mutate the database, never fabricate tracking numbers, and provide direct one-click navigation pills.
- **Low-Latency Intent Classification**: Zero-cost, CPU-bound ML intent classifier (~1-2ms on standard CPU) across 18 specialized domain intents with dynamic confidence thresholding and graceful fallback.
- **22+1 Official Languages of India**: Full support for all 22 languages recognized under the 8th Schedule of the Constitution of India plus English, with real-time clickable dropdown and instant search filter.
- **Zero-Delay Mental Health Crisis Guardrail**: Asymmetric safety thresholding for `distress_support` ($\ge 99\%$ recall target) triggering immediate confidential escalation (Tele-MANAS & Crisis Counseling) without ever routing to cloud LLMs.
- **Row-Level Access Control (RLAC) & Prompt Injection Defense**: Hardened security boundaries preventing cross-student record access, unauthorized queries, and prompt injection attempts before model inference.

---

## System Architecture

```
Student Query (Browser / Mobile)
          │
          ▼
[Next.js 16 Frontend on Vercel] ──── NEXT_PUBLIC_BACKEND_URL ───┐
                                                                │
                                                                ▼
                                              [FastAPI Backend on Render]
                                                                │
          ┌─────────────────────────────────────────────────────┤
          │                                                     │
          ▼                                                     ▼
[1. Security & RLAC Guardrail]                        [2. Distress Safety Filter]
(PII Redaction, Prompt Injection Defense)              (Immediate Tele-MANAS Escalation)
          │                                                     │
          └──────────────────────────┬──────────────────────────┘
                                     │
                                     ▼
                     [3. Hybrid Intent Classifier]
                     (TF-IDF + Logistic Regression, CPU)
                                     │
                                     ▼
                     [4. 23-Tool Registry & Service Graph]
                     ├── Attendance, Marks, Timetable, Fees (RLAC)
                     ├── Central Library Sunday Hours (09:00 - 17:00)
                     ├── Decentralized Hostel Dining (Ground Floor)
                     ├── Synchronized Hostel Shuttle Buses
                     ├── Dijkstra Shortest Path Navigation (23 Nodes)
                     └── Lost ID Replacement 2-Phase State Machine
                                     │
                                     ▼
                     [5. Neon Lakebase Postgres]
                     (315 Students, 4,944 Slots, 16 Relational Tables)
```

---

## Environment Variables Reference

### Backend (`BACKEND/.env` or Render Dashboard)
| Variable | Required? | Example / Default | Description |
| :--- | :---: | :--- | :--- |
| `ENVIRONMENT` | **Yes** | `production` (cloud) / `development` (local) | Enforces strict production security assertions. |
| `SECRET_KEY` | **Yes** | `[64-character random hex string]` | JWT encryption key. Production crashes if left default. |
| `DATABASE_URL` | **Yes** | `postgresql://user:pass@ep-...neon.tech/neondb?sslmode=require` | Pooled connection string to Neon Lakebase Postgres. |
| `DATABASE_URL_UNPOOLED` | Optional | `postgresql://user:pass@ep-...neon.tech/neondb?sslmode=require` | Direct connection string for schema migrations. |
| `USE_IN_MEMORY_DB` | **Yes** | `false` | Set to `false` to use live Neon PostgreSQL. |
| `USE_INTENT_CLASSIFIER` | **Yes** | `true` | Enables CPU-bound scikit-learn intent classifier. |
| `ENABLE_GEMINI` | Optional | `false` (default) / `true` | Toggles Google Gemini cloud reasoning fallback. |
| `GEMINI_API_KEY` | Optional | `AIzaSy...` | Required only if `ENABLE_GEMINI=true`. |
| `FRONTEND_ORIGINS` | Optional | `https://student-helpdesk-agent-five.vercel.app` | Allowed CORS origins for browser fetch requests. |

### Frontend (`FRONTEND/.env.local` or Vercel Dashboard)
| Variable | Required? | Example / Default | Description |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_BACKEND_URL` | **Yes** | `https://vigbot-api.onrender.com/api/v1` | Public HTTPS endpoint of the FastAPI backend. |

---

## Quick Start (Local Development)

### 1. Start the Backend API (FastAPI)
```bash
cd BACKEND

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source ../.venv/bin/activate

# Run Uvicorn server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*API runs at `http://localhost:8000` (Docs: `http://localhost:8000/docs`).*

### 2. Start the Frontend (Next.js)
```bash
cd FRONTEND
npm install
npm run dev
```
*Web app runs at `http://localhost:3000`.*

---

## Demo Student Login Credentials

Use these verified institutional student credentials to test login, attendance telemetry, marks, timetable, and conversational AI:

| Field | Primary Demo Credential | Alternative Demo Credential |
| :--- | :--- | :--- |
| **Roll Number / Username** | `24CSE001` | `24CSE002` |
| **Password** | `student123` | `student123` |
| **Student Name** | Asha Reddy | Rahul Verma |
| **Branch & Section** | B.Tech CSE (Section A) | B.Tech CSE (Section A) |
| **Attendance State** | Digital Electronics: 68.0% (Needs 14 classes for 75%) | Data Structures: 70.0% (Needs 8 classes for 75%) |

---

## License & Attribution

Developed for **Vignan's Foundation for Science, Technology and Research (VFSTR :: Vadlamudi)**.
All student records, policies, and calendar entries conform to institutional data protection regulations.
