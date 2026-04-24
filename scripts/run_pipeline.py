from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    scripts = [
        PROJECT_ROOT / "scripts" / "generate_data.py",
        PROJECT_ROOT / "scripts" / "run_analysis.py",
        PROJECT_ROOT / "scripts" / "run_evaluation.py",
    ]
    for script in scripts:
        subprocess.run([sys.executable, str(script)], check=True, cwd=PROJECT_ROOT)
    print("Pipeline complete.")


if __name__ == "__main__":
    main()

