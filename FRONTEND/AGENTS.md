<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# VIGBOT Frontend Guidelines

## Architecture Overview
- **Framework**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4.
- **Backend Connection**: FastAPI at `http://localhost:8000/api/v1` via `FRONTEND/src/lib/api-client.ts`.
- **Hybrid 3-Tier Routing**:
  - `Tier 1: Deterministic Guardrails & Domain Rules` (`routed_by: "rules"`)
  - `Tier 2: Local ML Intent Classifier (TF-IDF + LR)` (`routed_by: "classifier"` or `"classifier_pipeline_test"`)
  - `Tier 3: Cloud LLM Fallback (Gemini 3.5 Flash)` (`routed_by: "gemini"`): Student PII (name, roll_no, email) is anonymized to `[Authenticated Student]` before outbound dispatch.
- **Statutory Academic Rules**:
  - Minimum attendance threshold is **75%** (`0.75`).
  - Medical condonation window is between **65% and 74.9%** with approved medical certificate.
  - Attendance deficit recovery formula: `ceil((0.75 * held - attended) / 0.25)`.
- **Telemetry UI**:
  - `routed_by` is preserved on all assistant message objects and displayed in `AiHelpdeskPanel.tsx` with a live badge and verification modal.
