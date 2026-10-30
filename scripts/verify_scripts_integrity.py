import os
import sys
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
PYTHON_BIN = sys.executable

scripts = sorted([
    f.name for f in SCRIPTS_DIR.glob("*.py")
    if f.name != "verify_scripts_integrity.py"
])

print(f"Discovered {len(scripts)} scripts in {SCRIPTS_DIR}:")
for s in scripts:
    print(f"  - {s}")

print("\n" + "=" * 60)
print("PHASE 1: RUNNING ALL SCRIPTS FROM REPOSITORY ROOT")
print("=" * 60)

root_failures = []
for s in scripts:
    script_path = str(SCRIPTS_DIR / s)
    print(f"Running '{s}' from repo root... ", end="", flush=True)
    res = subprocess.run(
        [PYTHON_BIN, script_path],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.returncode == 0:
        print("✅ PASS")
    else:
        print(f"❌ FAIL (exit {res.returncode})")
        print("--- STDERR ---")
        print(res.stderr[:500])
        print("--- STDOUT ---")
        print(res.stdout[:500])
        root_failures.append(s)

print("\n" + "=" * 60)
print("PHASE 2: RUNNING ALL SCRIPTS FROM INSIDE SCRIPTS/ DIRECTORY")
print("=" * 60)

sub_failures = []
for s in scripts:
    print(f"Running '{s}' inside scripts/... ", end="", flush=True)
    res = subprocess.run(
        [PYTHON_BIN, s],
        cwd=str(SCRIPTS_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res.returncode == 0:
        print("✅ PASS")
    else:
        print(f"❌ FAIL (exit {res.returncode})")
        print("--- STDERR ---")
        print(res.stderr[:500])
        print("--- STDOUT ---")
        print(res.stdout[:500])
        sub_failures.append(s)

print("\n" + "=" * 60)
print("BATCH SCRIPTS INTEGRITY AUDIT SUMMARY")
print("=" * 60)
print(f"Total Scripts Tested:       {len(scripts)}")
print(f"Repo Root Failures:         {len(root_failures)}")
print(f"Scripts Subdir Failures:    {len(sub_failures)}")

if root_failures:
    print(f"Failed in root: {root_failures}")
if sub_failures:
    print(f"Failed in scripts/: {sub_failures}")

if not root_failures and not sub_failures:
    print("\n🎉 ALL 20 SCRIPTS PASSED COMPILATION, EXECUTION, AND DUAL-LOCATION INVOCATION WITH ZERO ERRORS!")
    sys.exit(0)
else:
    sys.exit(1)

