# VIGBOT Vibe Code Simplifier & Refactoring Suite

This folder provides a complete, turnkey toolkit to **audit, clean, pack, and safely refactor** AI-generated code in the VIGBOT project.

---

## 📁 What is in this Folder?

| File | Purpose |
| :--- | :--- |
| **`pack.ps1`** | Packs the codebase into a clean, token-counted context file using Repomix. |
| **`clean_code.py`** | Scans Python and TypeScript for vibe debt (long functions, debug statements, whitespace). |
| **`test_gate.ps1`** | Safety gate that runs backend pytest + frontend lint to verify zero regressions. |
| **`INSTRUCTIONS.md`** | Rules automatically injected into repomix packs to prevent AI from breaking RLS or safety. |
| **`PROMPTS.md`** | Ready-to-use prompts for AI refactoring sessions. |
| **`.aider.conf.yml`** | Ready configuration for Aider CLI pair programming with automated git rollback. |
| **`configs/`** | Targeted repomix profiles for `backend` and `frontend`. |
| **`output/`** | Destination directory where packed context markdown files are generated. |

---

## 🚀 Quick Start Workflows

### 1. Audit Code for Vibe Debt
Run the Python auditor to see which functions have grown too long or have lingering debug statements:
```powershell
python tools/vibe-simplifier/clean_code.py
```
*(To automatically clean up trailing whitespace noise, append `--autofix`)*:
```powershell
python tools/vibe-simplifier/clean_code.py --autofix
```

---

### 2. Pack Code for AI Simplification (Repomix)
Create a single, token-optimized context file to feed into Antigravity, Claude, or ChatGPT:

- **Pack Backend Only** (Python API, Agent, Database):
  ```powershell
  .\tools\vibe-simplifier\pack.ps1 -Target backend
  ```
  *Generates:* `tools/vibe-simplifier/output/backend-packed.md`

- **Pack Frontend Only** (Next.js, TypeScript, React):
  ```powershell
  .\tools\vibe-simplifier\pack.ps1 -Target frontend
  ```
  *Generates:* `tools/vibe-simplifier/output/frontend-packed.md`

- **Pack Entire Project**:
  ```powershell
  .\tools\vibe-simplifier\pack.ps1 -Target all
  ```
  *Generates:* `tools/vibe-simplifier/output/vigbot-packed.md`

---

### 3. Refactor with Prompt Guidance
1. Open [`PROMPTS.md`](file:///c:/StudentHelpdesk/tools/vibe-simplifier/PROMPTS.md).
2. Copy the relevant refactoring prompt (e.g. *Prompt 1: De-nesting & Early Returns* or *Prompt 2: Modularize Intent Handlers*).
3. Provide the generated pack from `tools/vibe-simplifier/output/` to your AI assistant.

---

### 4. Verify Quality Gate
After applying any AI-generated refactoring edits, always run the safety verification gate:
```powershell
.\tools\vibe-simplifier\test_gate.ps1
```
This ensures that all backend pytest suites (including Row-Level Security, Distress Safety, and Intent Handlers) and frontend ESLint rules pass 100% cleanly before committing.
