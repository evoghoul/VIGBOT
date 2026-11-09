# VIGBOT System & Evaluation Report: Empirical Facts

This document records the exact, empirical facts and benchmark metrics of the VIGBOT system extracted directly from the repository, database artifacts, and execution scripts. No values are estimated or invented. Items that do not exist in the repository are explicitly marked **NOT AVAILABLE**.

---

## 1. Final Intent Classifier

| Parameter / Metric | Empirical Value | Source / Verification Path |
| :--- | :--- | :--- |
| **Pipeline Type** | `FeatureUnion` (`word_tfidf` + `char_tfidf`) $\to$ `LogisticRegression` | `BACKEND/artifacts/intent_model.joblib` |
| **Word n-gram range** | `(1, 2)` | `BACKEND/artifacts/intent_train_metadata.json` |
| **Char n-gram range** | `(2, 5)` (`analyzer="char_wb"`) | `BACKEND/artifacts/intent_train_metadata.json` |
| **Regularization C** | `5.0` | `BACKEND/artifacts/intent_train_metadata.json` |
| **Class Weight** | `"balanced"` | `BACKEND/artifacts/intent_train_metadata.json` |
| **Solver & Max Iterations** | `solver="lbfgs"`, `max_iter=1000` | `ml/train_intent.py` |
| **Model Artifact File Size** | **5,539,788 bytes** (5,409.95 KB / 5.28 MB) | `BACKEND/artifacts/intent_model.joblib` |
| **Status in intent_config.json** | `"PRELIMINARY"` (Warning: `"PRELIMINARY: incomplete data"`) | `BACKEND/artifacts/intent_config.json` |
| **General Threshold** | `0.2` | `BACKEND/artifacts/intent_config.json` |
| **Distress Threshold** | `0.1` | `BACKEND/artifacts/intent_config.json` |
| **Out of Scope Threshold** | `0.5` | `BACKEND/artifacts/intent_config.json` |

### Cross-Validation Scores (Leave-One-Author-Out)
Leave-One-Author-Out (LOAO) validation across the 3 human training authors:
- **Mean Validation Macro-F1**: `0.8097`
- Held-out **aman**: Macro-F1 = `0.7878` (0.7878379176324111)
- Held-out **pragna**: Macro-F1 = `0.8547` (0.854677521514956)
- Held-out **sirisha**: Macro-F1 = `0.7865` (0.7865197550705295)

---

## 2. Dataset Row Counts

- **Starter Rows in `data/intents.csv`**: **239** rows (all `author="agent"`).
- **Total Dataset Size**: **2,304** rows (Training: 1,964 rows, Held-out Test: 340 rows).

### Row Counts per Author
| Author | Training Rows | Test Rows | Total Rows | Role / Source |
| :--- | :---: | :---: | :---: | :--- |
| `agent` | 239 | 0 | 239 | Seed starter corpus (`data/intents.csv`) |
| `aman` | 376 | 0 | 376 | Human Author (Student Helpdesk) |
| `clinc150` | 200 | 0 | 200 | Public NLU Benchmark Out-of-Scope subset |
| `massive` | 450 | 0 | 450 | Amazon MASSIVE Public Corpus (Multilingual Smalltalk & Out-of-Scope) |
| `pragna` | 371 | 0 | 371 | Human Author (Academics & Regulations) |
| `sirisha` | 328 | 0 | 328 | Human Author (Campus Life & Services) |
| `sridhar` | 0 | 340 | 340 | Held-Out Independent Test Author |
| **Total** | **1,964** | **340** | **2,304** | |

### Row Counts per Topic (Intent)
| Topic / Intent | Training Rows | Test Rows (`sridhar`) | Total Rows |
| :--- | :---: | :---: | :---: |
| `attendance` | 67 | 20 | 87 |
| `circulars` | 79 | 20 | 99 |
| `clubs` | 75 | 20 | 95 |
| `curriculum` | 75 | 20 | 95 |
| `distress_support` | 105 | 15 | 120 |
| `events` | 54 | 20 | 74 |
| `exams` | 69 | 20 | 89 |
| `faculty` | 76 | 20 | 96 |
| `fees` | 72 | 20 | 92 |
| `greeting_smalltalk` | 259 | 15 | 274 |
| `hostel` | 52 | 20 | 72 |
| `library` | 69 | 20 | 89 |
| `marks` | 74 | 20 | 94 |
| `out_of_scope` | 518 | 15 | 533 |
| `policy_bylaws` | 74 | 15 | 89 |
| `services` | 125 | 20 | 145 |
| `timetable` | 71 | 20 | 91 |
| `transport` | 50 | 20 | 70 |
| **Total** | **1,964** | **340** | **2,304** |

### Row Counts per Language
| Language Code | Language | Training Rows | Test Rows (`sridhar`) | Total Rows |
| :--- | :--- | :---: | :---: | :---: |
| `en` | English | 910 | 340 | 1,250 |
| `hi` | Hindi (Devanagari) | 175 | 0 | 175 |
| `hinglish` | Hindi (Roman script) | 296 | 0 | 296 |
| `te` | Telugu (Telugu script) | 175 | 0 | 175 |
| `te_roman` | Telugu (Roman script) | 408 | 0 | 408 |
| **Total** | | **1,964** | **340** | **2,304** |

---

## 3. Test Results on the Held-Out File (`sridhar`)

- **Run Status**: **PRELIMINARY** (explicitly marked with warning: `"PRELIMINARY: incomplete data"` in `BACKEND/artifacts/preliminary_results_intent.json` and `intent_config.json`).
- **Test File**: `data/sridhar_intents.csv` (340 queries written by independent author `sridhar`).

### Performance Summary & Comparison (N=200 Standard Benchmark Subset)
| Model / System | Accuracy (95% CI) | Macro-F1 (95% CI) | Distress Recall | Coverage | Latency (Mean / p50 / p95) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Classifier Benchmark (N=200)** | **0.8400** [0.7900, 0.8900] | **0.8370** [0.7772, 0.8833] | **0.7778** | **1.0000** (100%) | 1.28 ms / 1.25 ms / 1.49 ms |
| **Rules-Only Baseline (N=200)** | **0.4900** [0.4250, 0.5600] | **0.5059** [0.4342, 0.5620] | **0.1111** | **0.7050** (59 unmatched) | 0.01 ms / 0.01 ms / 0.01 ms |
| **Paired Difference ($\Delta$)** | **+0.3500** [+0.2750, +0.4250] | **+0.3311** [+0.2593, +0.4070] | **+0.6667** | **+0.2950** | — |

*Full Test Set Evaluation (N=340 questions, author: `sridhar`): Accuracy = **0.8647** (raw) / **0.8618** (with post-threshold routing), Macro-F1 = **0.8618** (raw) / **0.8580**, Distress Recall = **0.8000** (80.0%).*

### Per-Topic Report on `sridhar` Full Test Set (N=340)
| Topic / Intent | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| `attendance` | 1.0000 | 0.9000 | 0.9474 | 20 |
| `circulars` | 0.9091 | 1.0000 | 0.9524 | 20 |
| `clubs` | 1.0000 | 1.0000 | 1.0000 | 20 |
| `curriculum` | 0.9000 | 0.9000 | 0.9000 | 20 |
| `distress_support` | 0.8571 | 0.8000 | 0.8276 | 15 |
| `events` | 0.9444 | 0.8500 | 0.8947 | 20 |
| `exams` | 0.8667 | 0.6500 | 0.7429 | 20 |
| `faculty` | 1.0000 | 0.7500 | 0.8571 | 20 |
| `fees` | 0.8182 | 0.9000 | 0.8571 | 20 |
| `greeting_smalltalk` | 0.8235 | 0.9333 | 0.8750 | 15 |
| `hostel` | 0.8947 | 0.8500 | 0.8718 | 20 |
| `library` | 0.8261 | 0.9500 | 0.8837 | 20 |
| `marks` | 0.9444 | 0.8500 | 0.8947 | 20 |
| `out_of_scope` | 0.7500 | 0.8000 | 0.7742 | 15 |
| `policy_bylaws` | 0.6667 | 0.6667 | 0.6667 | 15 |
| `services` | 0.5714 | 0.8000 | 0.6667 | 20 |
| `timetable` | 0.9048 | 0.9500 | 0.9268 | 20 |
| `transport` | 1.0000 | 0.9500 | 0.9744 | 20 |
| **Accuracy** | | | **0.8647** | 340 |
| **Macro Average** | **0.8710** | **0.8611** | **0.8618** | 340 |
| **Weighted Average** | **0.8766** | **0.8647** | **0.8663** | 340 |

### Top 5 Confusions with Example Questions
Extracted directly from `BACKEND/artifacts/preliminary_misclassified.csv`:
1. **`marks` $\to$ `services` (3 instances)**:
   - *"How do I apply for revaluation of my answer script?"*
   - *"Can I get a copy of my evaluated answer sheet?"*
   - *"What should I do if my result shows absent by mistake?"*
2. **`attendance` $\to$ `policy_bylaws` (2 instances)**:
   - *"How much attendance is required to write exams?"*
   - *"How can I apply for attendance condonation?"*
3. **`exams` $\to$ `policy_bylaws` (2 instances)**:
   - *"Can I get the rules for the examination hall?"*
   - *"What happens if I miss an internal exam?"*
4. **`curriculum` $\to$ `out_of_scope` (2 instances)**:
   - *"Which programming languages are taught this year?"*
   - *"What are the important topics in the current unit?"*
5. **`faculty` $\to$ `timetable` (2 instances)**:
   - *"Who handles the Data Structures lab?"*
   - *"Which lecturer is assigned to our lab batch?"*

---

## 4. Re-Run of the 9 Reproduction Queries on the Current System

Executed on the live backend orchestrator (`VIGBOTOrchestrator.process_message`) with authenticated session `cccccccc-0000-0000-0000-000000000001` (Asha Reddy):

### 1. "hostel bus timing"
- **Category**: `HOSTEL` | **Source Agent**: `VIGBOT (Hostel & Mess Services Guide)` | **Routed By**: `classifier` (via capability registry)
- **Final Answer**:
> 🏠 **Hostel & Dining Services:**
>
> Hostel dining facilities at VFSTR are decentralized: there is no single central mess building; instead, every individual hostel (including Vignan Vihar, KM, AR, AP, and Priyadarshini) contains its own internal mess on the ground floor. Which hostel do you reside in so I can provide your exact mess details? Dinner across all hostels is served from 7:30 PM to 9:00 PM.
>
> • **Dining Schedule:** Breakfast (07:15 - 08:45 AM) | Lunch (12:15 - 01:45 PM) | Dinner (07:30 - 09:00 PM)
> • **Curfew & Biometrics:** Boys Hostel: 09:30 PM | Girls Hostel: 08:30 PM (Biometric punch mandatory)
> • **Outpass Protocol:** Weekend outing requests must be submitted by Friday 05:00 PM with warden approval.
>
> You can apply for outpasses and view dining menus in the **Hostel & Mess** tab.

### 2. "is the library open on sunday"
- **Category**: `LIBRARY` | **Source Agent**: `VIGBOT (Central Library Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 📚 **Central Library Information & Schedule:**
>
> Yes, the Central Library is open on Sundays from 09:00 AM to 05:00 PM (09:00 - 17:00) for reading rooms and digital study spaces, though book circulation counters remain closed.
>
> • **Regular Hours (Mon-Fri):** 08:00 AM - 10:00 PM (Reading Hall) | 09:00 AM - 06:00 PM (Lending Counter)
> • **Weekend Hours:** Saturday: 08:00 AM - 08:00 PM | Sunday: 09:00 AM - 05:00 PM (Reading Hall & Digital Access Only)
> • **Digital Resources:** 10,000+ IEEE/Springer e-journals accessible on campus LAN.
>
> You can explore library catalog and digital repositories in the **Library** tab.

### 3. "where is the mess and what time is dinner"
- **Category**: `MAP` | **Source Agent**: `VIGBOT (Campus Map & Navigation Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 📍 **Vignan Vihar Boys Hostel Location & Campus Directions:**
>
> Vignan Vihar is the 1st-year boys hostel (featuring an internal ground-floor mess), located directly in front of N-Block on Path Beta (260.0 meters from Main Gate (Node 0)).
>
> **🚶 Turn-by-Turn Walking Route from Main Gate (Node 0) (260.0m):**
> • Step 1: Proceed straight along the main tree-lined road from the Main Gate. (50m)
> • Step 2: Continue straight along Path Alpha past Intersection 1; NTR Vignan Library is on your right. (60m)
> • Step 3: Continue straight along Path Alpha; MHP Campus Canteen is on your right. (40m)
> • Step 4: Continue straight; Zest is immediately adjacent to MHP Canteen on the right. (25m)
> • Step 5: Turn right just beside Zest into Path Beta towards N-Block. (15m)
> • Step 6: Proceed along Path Beta; N-Block is located just beside Zest. (50m)
> • Step 7: Vignan Vihar Boys Hostel is situated directly in front of N-Block. (20m)
>
> You can also explore the interactive 2D layout in the **Campus Map** tab.

### 4. "how do i report a lost id card"
- **Category**: `LOST_AND_FOUND` | **Source Agent**: `VIGBOT (Lost & Found Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 🔍 **Lost & Found Campus Repository:**
>
> To replace a lost student ID card, follow the official two-phase procedure: first submit a digital report on the sidebar's Lost & Found board, then report physically to the Administrative Office in H-Block (ground floor, left hallway) to submit the form, collect Hostel & Chief Warden signatures, and remit the ₹100 penalty fee.
>
> • **Report Lost Item:** Click the 'Report Item' button to log details (item type, location last seen, contact).
> • **Found Something?** Submit a report or deposit found valuables (wallets, phones, ID cards) at Chief Security Office, Main Gate.
> • **Claim Process:** Bring your university student ID card and verify item specifics to claim.
>
> You can browse active listings or log an item in the **Lost & Found** tab.

### 5. "which club should i join for robotics"
- **Category**: `CLUBS` | **Source Agent**: `VIGBOT (Clubs & Extracurriculars Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 🎭 **Student Clubs & Extracurricular Communities:**
>
> For robotics, artificial intelligence, and hardware prototyping, you should join the AI Innovation Club (Technical), based out of the N-Block High-Performance AI Lab.
>
> • **Technical:** AI Innovation Club, Coding & Algorithm Chapter, Robotics & Automation
> • **Cultural & Arts:** Symphony Music Club, Natya Dance Troupe, Vignan Shutterbugs (Photography)
> • **Social & Leadership:** NSS Unit, NCC Wing, Green Earth Environmental Society
>
> You can explore club events and submit joining applications in the **Clubs & Communities** tab.

### 6. "book seminar hall tomorrow"
- **Category**: `BOOKINGS` | **Source Agent**: `VIGBOT (Facility Bookings Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 🏟️ **Campus Facility Booking & Venues:**
>
> Campus facilities available for student club and academic bookings include Seminar Hall 1 (Capacity: 250), Main Auditorium (Capacity: 1200), Open Air Theatre (Capacity: 2500), and the Indoor Sports Complex. Requests require faculty mentor endorsement 48 hours in advance.
>
> • **Seminar Halls 1 & 2:** Capacity: 250 | Audio-visual projector & air-conditioned
> • **Main Convocation Auditorium:** Capacity: 1,500 | Large stage, professional acoustics
> • **Sports Complex:** Cricket Ground, Outdoor Basketball Courts, Indoor Badminton Arena
> • **Advance Reservation:** Facility booking requests must be submitted at least 48 hours prior with faculty coordinator sign-off.
>
> You can check live slot availability and reserve venues in the **Facility Booking** tab.

### 7. "bus from guntur to college time"
- **Category**: `TRANSPORT` | **Source Agent**: `VIGBOT (Campus Transport & Bus Tracking Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 🚌 **Campus Transport & Bus Schedule:**
>
> VFSTR operates 4 major city transit routes: Route 1 (Guntur Express: 7:35 AM arrival, 4:45 PM return), Route 2 (Vijayawada Express: 7:30 AM arrival), Route 3 (Tenali Shuttle: 7:40 AM arrival), and Route 4 (Chilakaluripet: 7:30 AM arrival).
>
> • **Route 1 (Guntur):** Leaves 06:45 AM | Returns 04:45 PM (Old Bus Stand - Collectorate - Campus)
> • **Route 2 (Vijayawada):** Leaves 06:30 AM | Returns 04:45 PM (Benz Circle - Auto Nagar - Campus)
> • **Route 3 (Tenali):** Leaves 07:00 AM | Returns 04:45 PM (Railway Station - Chenchupet - Campus)
> • **Route 4 (Mangalagiri):** Leaves 07:10 AM | Returns 04:45 PM (Main Bazaar - NRI Hospital - Campus)
>
> You can track bus routes and live transport passes in the **Transport** tab.

### 8. "what is my attendance in dbms and how many classes to reach 75"
- **Category**: `PERSONAL_DATA` | **Source Agent**: `VIGBOT (Academic Advising & Attendance Engine)` | **Routed By**: `rules` (Exam eligibility guardrail)
- **Final Answer**:
> Based on your verified university records for **Digital Electronics (CS302)**:
>
> • **Current Attendance:** **68.0%** (34 out of 50 classes attended).
> • **Exam Eligibility Status:** ⚠️ **Currently Below 75% Mandatory Cutoff** (Clause 4.2 of Academic Regulations R23).
>
> ### 1. Attendance Recovery Calculation:
> • **Consecutive Classes Needed:** You must attend the **next 14 consecutive classes** without absence.
> • **Projected Metric:** After attending 14 consecutive lectures, your attendance will reach **75.0%** (48/64 classes), restoring regular exam eligibility.
>
> ### 2. Medical Condonation Eligibility (Clause 4.2):
> • Because your attendance is **68.0%**, you fall safely within the **65.0% - 74.9% condonation bracket**.
> • Students in this bracket may appear for summative examinations upon submitting medical proof approved by the Dean of Academics and paying the condonation fee.
>
> **Recommendation:** Attend all upcoming classes consistently to cross 75% naturally before the 2026-11-20 cutoff date.

### 9. "where is u block"
- **Category**: `MAP` | **Source Agent**: `VIGBOT (Campus Map & Navigation Guide)` | **Routed By**: `classifier`
- **Final Answer**:
> 📍 **U-Block Location & Campus Directions:**
>
> U-Block houses the School of Law and Management (BBA & Law students), located 325.0 meters from Main Gate (Node 0) positioned directly behind N-Block and adjacent to Convocation Hall past Intersection 2.
>
> **🚶 Turn-by-Turn Walking Route from Main Gate (Node 0) (325.0m):**
> • Step 1: Proceed straight along the main tree-lined road from the Main Gate. (50m)
> • Step 2: Continue straight along Path Alpha past Intersection 1; NTR Vignan Library is on your right. (60m)
> • Step 3: Continue straight along Path Alpha; MHP Campus Canteen is on your right. (40m)
> • Step 4: Continue straight; Zest is immediately adjacent to MHP Canteen on the right. (25m)
> • Step 5: Turn right just beside Zest into Path Beta towards N-Block. (15m)
> • Step 6: Proceed along Path Beta; N-Block is located just beside Zest. (50m)
> • Step 7: Continue along the road past N-Block along Path Gamma to Intersection 2. (40m)
> • Step 8: Bypass Intersection 2 and continue straight behind N-Block; U-Block (Law & BBA) is straight ahead. (45m)
>
> You can also explore the interactive 2D layout in the **Campus Map** tab.

---

## 5. Architectural & Code Audit

| Component | Exists? | File Path | Function / Method | Architectural Details |
| :--- | :---: | :--- | :--- | :--- |
| **Top-2 Tool Selection** | **NO** | `NOT AVAILABLE` | `NOT AVAILABLE` | The current system dispatches via single-match deterministic capability resolution (`find_matching_capability`), keyword routing, or single ML classification (`route_classified_intent`). No top-2 ranking or multi-candidate selection function exists. |
| **Answer-First Templates** | **YES** | `BACKEND/app/agent/tool_registry.py` | `ToolRegistry.get_home_overview`, `get_attendance_records`, `get_campus_location_and_navigation`, and all 23 tool methods | Enforces the "Answer-First Rule" (Rule 1, line 6 of `tool_registry.py`), guaranteeing direct factual answers in the initial sentence before bulleted details. |
| **Entity Extraction** | **YES** | `BACKEND/app/agent/nlu_engine.py`<br>`BACKEND/app/agent/tool_registry.py` | `NLUEngine.extract_subject(cls, text: str)`<br>`CampusGraphService.resolve_node_id(cls, landmark_query: str)` | Extracts academic subject entities (DLD, DS, DBMS, OOPS, AI), landmark nodes for navigation, and tracking ticket IDs via regex in `UniversalNLU.resolve_and_execute`. |
| **Document Search (BM25 or similar)** | **YES** | `BACKEND/app/research/vignan_rag.py`<br>`BACKEND/app/tools/knowledge_tool.py` | `VignanHybridRetriever.retrieve(cls, query: str, top_k: int = 3, ...)`<br>`search_policies_and_circulars` | Implements BM25 lexical token matching and TF-IDF scoring combined with category filtering over official university bylaws, circulars, and handbooks. |
| **Grounding Guard** | **YES** | `BACKEND/app/agent/grounding_guard.py` | `verify_numeric_faithfulness(reply_text, student_context)`<br>`enforce_grounding_or_fallback(...)` | Deterministically validates all percentages, currency amounts, class counts, and CGPA metrics against the authorized DB session, substituting hallucinated metrics with DB fallbacks. |
| **LLM Call (Gemini, Ollama or other)** | **YES** | `BACKEND/app/agent/llm_client.py`<br>`BACKEND/scripts/fine_tune_llama3.py` | `LLMClient._send_gemini_chat`<br>`LLMClient._send_groq_chat`<br>`LLMClient.chat_with_history` | Implements multi-tier cloud inference for Google Gemini (`gemini-2.5-flash`, `gemini-1.5-flash`) and Groq (`qwen/qwen3.8-27b`), falling back to local `MockAcademicEngine`. Ollama is used in local fine-tuning scripts. |

---

## 6. Exact Technology Versions & Environment

### Software & Package Versions
| Package / Runtime | Exact Version | Verification Source |
| :--- | :--- | :--- |
| **Python** | `3.12.10` | `BACKEND/.venv/Scripts/python.exe --version` |
| **FastAPI** | `0.141.1` | `pip show fastapi` in virtual environment |
| **scikit-learn** | `1.9.1` | `pip show scikit-learn` in virtual environment |
| **numpy** | `2.5.3` | `pip show numpy` in virtual environment |
| **scipy** | `1.18.1` | `pip show scipy` in virtual environment |
| **joblib** | `1.6.0` | `pip show joblib` in virtual environment |
| **pytest** | `9.1.1` | `pytest --version` |
| **Next.js** | `16.3.4` | `FRONTEND/package.json` (`next`) |
| **React** | `19.2.8` | `FRONTEND/package.json` (`react`) |
| **Tailwind CSS** | `4.3.3` | `FRONTEND/package.json` (`tailwindcss`) |

### Hosting Platforms Used
- **Frontend**: **Vercel** (`student-helpdesk-agent-five.vercel.app`)
- **Backend API**: **Render** (`vigbot-api.onrender.com` Docker deployment)
- **Database**: **Neon PostgreSQL** (Cloud Serverless Postgres with pgvector/lakebase extensions)

### Database Table Counts
- **Canonical SQLite (`database/vigbot.db`)**: **50 tables**
- **Frontend Bundled SQLite (`FRONTEND/vigbot.db`)**: **49 tables**
- **Neon Cloud PostgreSQL**: Matches canonical schema with 50 operational relational tables.

---

## 7. Test, Audit & Attack Counts

All counts executed from real scripts and verified artifacts:

### 1. Pytest Test Suite Summary
- **Command**: `& "C:\StudentHelpdesk\BACKEND\.venv\Scripts\pytest.exe" --collect-only BACKEND/tests`
- **Collected Count**: **134 items** (`1 deselected`, **133 selected**) across 12 test modules.
- **Fast Unit Test Execution** (`tests/test_data_guardrails.py`): **10 passed in 0.67s** (100% pass).
- **Feedback Remediation Suite** (`tests/test_feedback_remediation.py`): **4 passed in 36.24s** (100% pass).
- **Intent Classifier Suite** (`BACKEND/tests/test_intent_classifier.py`): **14 passed, 2 failed in 353.71s** (KeyError on mock `llm_provider` dictionary and card type expectation).

### 2. Adversarial False-Action Safety Suite
- **Command**: `& "C:\StudentHelpdesk\BACKEND\.venv\Scripts\python.exe" scripts/run_adversarial_safety_suite.py`
- **Artifact**: `BACKEND/artifacts/false_action_audit.json`
- **Total Adversarial Attempts**: **15**
- **False Write Operations Detected**: **0** (0/15)
- **False Success Confirmations**: **0** (0/15)
- **Stale Confirmation Attacks Defended**: **True** (100%)
- **Verdict**: **PASSED** (15 of 15 attempts blocked from unauthorized mutations or fabricated success confirmations).
- *(Complementary E6 RLAC Suite in `ml/evaluate_security_and_grounding.py`: **25** adversarial cross-student attacks tested, **25 blocked (100.0%)**, **0 unauthorized data leaks**).*

### 3. Numeric Faithfulness & Grounding Check
- **Command**: `& "C:\StudentHelpdesk\BACKEND\.venv\Scripts\python.exe" ml/evaluate_security_and_grounding.py`
- **Artifact**: `BACKEND/artifacts/security_and_grounding_results.json` (`experiment_e4`)
- **Number of Evaluated Queries (N)**: **30**
- **Faithful Grounded Matches**: **30**
- **Faithfulness Rate**: **100.0%** (30/30 matches; unverified count = 0; mean latency = 128.21 ms).

### 4. Distress Check on `data/crisis_test.csv`
- **Status**: **NOT AVAILABLE (file does not exist in repo)**
- **Verification**: `Test-Path data/crisis_test.csv` evaluated to `False`. In `BACKEND/artifacts/preliminary_results_intent.json` (line 224), `"crisis_test_evaluation": null`.
- *(On the held-out `sridhar` test split with 15 distress queries, distress support recall was **80.00%** [12/15 recalled] in the ML model and **100.0%** in deterministic safety guardrail `detect_distress`).*

---

## 8. Deployment URLs

| Service | URL | Status |
| :--- | :--- | :--- |
| **GitHub Repository** | `https://github.com/evoghoul/Student-Helpdesk-Agent.git` | Active Public Repository |
| **Live Production Demo** | `https://student-helpdesk-agent-five.vercel.app` | Live on Vercel |
| **Live Backend API** | `https://vigbot-api.onrender.com` | Live on Render |

