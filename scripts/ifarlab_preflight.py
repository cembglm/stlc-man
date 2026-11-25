"""Print a machine-readable ASRLab/IFARLAB readiness report without using MongoDB."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from services.ifarlab_readiness_service import readiness_report  # noqa: E402


def main() -> int:
    report = readiness_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
