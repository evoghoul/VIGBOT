"""
VIGBOT Vibe Code Cleaner & Debt Auditor
Scans Python backend and TypeScript frontend for:
- Long/monolithic functions (> 60 lines)
- Stray console.log / debugger statements in frontend
- Raw print() statements in backend (should use logger)
- Trailing whitespace & excess blank lines

Usage:
    python clean_code.py            # Audit mode (read-only)
    python clean_code.py --autofix  # Fix trailing whitespace & format safe items
"""

import os
import sys
import re
import argparse
from typing import List, Dict, Any

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "BACKEND", "app")
FRONTEND_DIR = os.path.join(ROOT_DIR, "FRONTEND", "src")

def audit_file(filepath: str) -> Dict[str, Any]:
    rel_path = os.path.relpath(filepath, ROOT_DIR)
    is_python = filepath.endswith(".py")
    is_ts = filepath.endswith((".ts", ".tsx"))

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    issues = []
    trailing_ws_count = 0
    consecutive_blank = 0
    max_consecutive_blank = 0

    curr_func = None
    curr_func_start = 0
    long_functions = []

    for idx, line in enumerate(lines, start=1):
        stripped_line = line.rstrip("\r\n")
        
        # Check trailing whitespace
        if line.endswith(" \n") or line.endswith("\t\n") or (stripped_line != line.rstrip()):
            trailing_ws_count += 1

        # Check consecutive blanks
        if not stripped_line.strip():
            consecutive_blank += 1
            if consecutive_blank > max_consecutive_blank:
                max_consecutive_blank = consecutive_blank
        else:
            consecutive_blank = 0

        # Python checks
        if is_python:
            # Check for raw print()
            if re.search(r"^\s*print\(", line) and not rel_path.startswith("ml"):
                issues.append((idx, "RAW_PRINT", "Found raw print() statement (prefer logging.getLogger)"))

            # Function tracking
            m = re.match(r"^\s*(?:async\s+)?def\s+([A-Za-z0-9_]+)\s*\(", line)
            if m:
                if curr_func and (idx - curr_func_start) > 60:
                    long_functions.append((curr_func, idx - curr_func_start))
                curr_func = m.group(1)
                curr_func_start = idx

        # TypeScript / JavaScript checks
        if is_ts:
            if re.search(r"console\.(?:log|debug)\(", line) and not any(x in filepath for x in ["api-client.ts", "verify-engine.ts"]):
                issues.append((idx, "CONSOLE_LOG", "Found console.log in UI code"))
            if "debugger;" in line:
                issues.append((idx, "DEBUGGER", "Found lingering debugger statement"))

            m = re.match(r"^\s*(?:export\s+)?(?:default\s+)?function\s+([A-Za-z0-9_]+)\s*\(", line)
            if m:
                if curr_func and (idx - curr_func_start) > 80:
                    long_functions.append((curr_func, idx - curr_func_start))
                curr_func = m.group(1)
                curr_func_start = idx

    return {
        "file": rel_path,
        "lines": len(lines),
        "trailing_ws": trailing_ws_count,
        "max_blank": max_consecutive_blank,
        "issues": issues,
        "long_functions": long_functions
    }

def fix_whitespace_in_file(filepath: str) -> int:
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    
    fixed_lines = [line.rstrip() + "\n" if line.strip() else "\n" for line in lines]
    if fixed_lines != lines:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)
        return 1
    return 0

def run_audit(autofix: bool = False):
    print("=" * 65)
    print("        VIGBOT Vibe Code Debt & Complexity Auditor")
    print("=" * 65)

    files_to_check = []
    for base_dir in [BACKEND_DIR, FRONTEND_DIR]:
        if not os.path.exists(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".py", ".ts", ".tsx")):
                    files_to_check.append(os.path.join(root, file))

    total_issues = 0
    total_long_funcs = 0
    files_with_ws = 0

    print(f"\nScanning {len(files_to_check)} source files across Frontend & Backend...\n")

    for fp in files_to_check:
        res = audit_file(fp)
        has_notable_issue = (
            len(res["issues"]) > 0 or 
            len(res["long_functions"]) > 0 or 
            res["trailing_ws"] > 10
        )

        if has_notable_issue:
            print(f"📄 {res['file']} ({res['lines']} lines)")
            if res["long_functions"]:
                for fn, length in res["long_functions"]:
                    print(f"   ⚠️  Long function '{fn}' ({length} lines) -> candidate for modularization")
                    total_long_funcs += 1
            if res["issues"]:
                for line_no, code, msg in res["issues"][:5]:
                    print(f"   ⚠️  Line {line_no} [{code}]: {msg}")
                    total_issues += 1
                if len(res["issues"]) > 5:
                    print(f"   ... and {len(res['issues']) - 5} more issues")
            if res["trailing_ws"] > 0:
                print(f"   ℹ️  {res['trailing_ws']} trailing whitespace lines")
                files_with_ws += 1
            print()

        if autofix and res["trailing_ws"] > 0:
            fix_whitespace_in_file(fp)

    print("-" * 65)
    print(f"Audit Summary:")
    print(f" - Long functions to simplify: {total_long_funcs}")
    print(f" - Vibe artifacts (logs/prints/debuggers): {total_issues}")
    print(f" - Files with whitespace noise: {files_with_ws}")
    if autofix:
        print(f" ✔ Fixed whitespace noise in {files_with_ws} files.")
    else:
        print(f" Tip: Run 'python clean_code.py --autofix' to clean whitespace automatically.")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VIGBOT Code Debt Auditor")
    parser.add_argument("--autofix", action="store_true", help="Automatically clean trailing whitespace")
    args = parser.parse_args()
    run_audit(autofix=args.autofix)
