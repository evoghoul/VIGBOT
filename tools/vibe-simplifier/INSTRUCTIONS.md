# VIGBOT Code Simplification & Refactoring Instructions

You are acting as a Senior Principal Software Architect auditing the VIGBOT codebase (Student Helpdesk AI Agent).
Your objective is to **simplify, refactor, and decouple** complex or bloated code that was generated iteratively during rapid "vibe coding" sessions.

---

### Non-Negotiable Architectural Invariants

1. **Safety & Distress Guardrail Preservation**:
   - The emergency counseling detection in `app/safety/distress_detector.py` and `app/agent/orchestrator.py` must NEVER be bypassed or delayed.
   - Crisis queries must always return immediate crisis hotline responses without calling any external LLM.

2. **Row-Level Security (RLS) & Student Session Boundaries**:
   - Every student query operates through `DatabaseSession(student_id=..., user_id=...)`.
   - Never allow a student to query or see attendance, marks, fees, or personal data belonging to another student ID.

3. **Deterministic Local Grounding**:
   - Numerical calculations (e.g. attendance percentage, classes needed for 75%, fee dues) must strictly use database facts and mathematical formulas from `grounding_guard.py` and `attendance_tool.py`. Never invent or estimate numbers.

4. **Zero API Signature Breaks**:
   - All FastAPI route signatures in `BACKEND/app/api/` and Next.js client methods in `FRONTEND/src/lib/api-client.ts` must maintain backwards compatibility.
   - All 130 automated unit tests in `BACKEND/tests/` must continue to pass cleanly.

---

### Simplification Targets

- **Eliminate Deep Nesting (Arrow Anti-Pattern)**: Convert nested `if/else` ladders into early guard returns (`if not valid: return`).
- **Break Down Monolithic Functions**: Split functions over 50 lines into private, well-named single-purpose helper functions.
- **De-Duplicate Logic**: Unify repeated database query setups, JSON serialization routines, and error-handling blocks.
- **Strip Vibe Artifacts**: Remove commented-out code, temporary debug `print()` / `console.log()` statements, and orphaned imports.
- **Decouple Modules**: Avoid circular dependencies between `orchestrator.py`, `nlu_engine.py`, and `database.py`.
