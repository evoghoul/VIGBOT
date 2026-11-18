# VIGBOT AI Refactoring & Simplification Prompts

Use these prompts when passing packed code (`backend-packed.md` or `frontend-packed.md`) to Antigravity, Claude, or ChatGPT.

---

### Prompt 1: De-nesting & Early Returns (Arrow Anti-Pattern)
```text
I have attached the packed context of VIGBOT. 
Please audit the following file: [PATH_TO_FILE, e.g. BACKEND/app/agent/orchestrator.py].
Refactor deeply nested if/else statements and pyramid logic into early guard returns (guard clauses).
Constraints:
- Do NOT alter any method signatures or return types.
- Maintain existing Row-Level Security (session) checks.
- Keep all existing comments and documentation.
- Output the refactored code with a concise summary of changes.
```

---

### Prompt 2: Modularize Monolithic Intent Handlers
```text
In BACKEND/app/agent/nlu_engine.py, classify_and_reason() has grown excessively long due to multiple iterative additions.
Please refactor this method by:
1. Extracting discrete intent routing blocks into focused private helper methods (e.g. _handle_policy_route, _handle_academic_route).
2. Preserving the exact order of precedence: Safety Distress Guard -> Privacy Injection -> Learned Remediation -> Universal NLU -> Intent Classifier.
3. Ensuring zero external API calls are introduced.
```

---

### Prompt 3: Frontend Component Cleanup
```text
Please inspect FRONTEND/src/app/page.tsx and FRONTEND/src/components/chat/ChatContainer.tsx from the attached pack.
Refactor the components to:
1. Extract repetitive inline SVG icons into reusable components or Lucide icons.
2. Remove any remaining console.log debug statements.
3. Clean up unused state hooks or redundant useEffect dependencies.
4. Ensure full TypeScript strict mode compliance and Next.js 16 compatibility.
```

---

### Prompt 4: Safe Dead-Code Removal
```text
Audit the attached codebase slice for orphaned helper functions, unused imports, and unreferenced constants.
List all candidates for removal before deleting anything.
Verify that none of the candidates are referenced by dynamic getattr(), SQL queries, or tests in BACKEND/tests/.
```
