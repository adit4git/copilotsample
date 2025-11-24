# Validation Script for Generic Context Pack

print("=== VALIDATION RESULTS ===")

import os

required = [
    "analysis/context/instructions",
    "analysis/context/templates",
    "analysis/context/prompts",
    "analysis/output",
    ".copilot.json"
]

missing = []
for r in required:
    if not os.path.exists(r):
        missing.append(r)

if missing:
    print("Missing required paths:")
    for m in missing:
        print(" -", m)
else:
    print("All required paths are present.")

# Check instruction files
instruction_dir = "analysis/context/instructions"
if os.path.isdir(instruction_dir):
    files = os.listdir(instruction_dir)
    if not files:
        print("WARNING: No instruction files found.")
    else:
        print("Instruction files:", files)
else:
    print("Instruction folder missing.")

print("==========================")
