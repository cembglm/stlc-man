#!/usr/bin/env python3
"""Validate an STLC-generated Python test before IFARLAB dispatch.

This CLI is the operator-facing entry point requested by the IFARLAB handoff.
It delegates to the same combined validator used by the backend immediately
before SCP, so command-line and application decisions cannot drift apart.

Usage:
    python scripts/validate_generated.py generated.py [--caps config/robot_capabilities.json] [--json]

Exit codes:
    0  validation passed (warnings may be present)
    1  generated code contains blocking validation errors
    2  generated code does not parse or the capability contract is unusable
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPOSITORY_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.robot_capability_service import (  # noqa: E402
    RobotCapabilityError,
    load_robot_capability_file,
    validate_generated_code_report,
)


def validate(source: str, caps_path: Path) -> Tuple[List[str], List[str]]:
    """Return blocking errors and non-blocking warnings for generated code."""
    ast.parse(source)
    contract, _raw = load_robot_capability_file(caps_path)
    report = validate_generated_code_report(source, contract)
    return report["errors"], report["warnings"]


def _payload(errors: List[str], warnings: List[str]) -> Dict[str, Any]:
    return {
        "errors": [{"msg": message} for message in errors],
        "warnings": [{"msg": message} for message in warnings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--caps",
        type=Path,
        default=REPOSITORY_ROOT / "config" / "robot_capabilities.json",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        source = args.file.read_text(encoding="utf-8", errors="replace")
        errors, warnings = validate(source, args.caps)
    except SyntaxError as exc:
        message = f"Python syntax error at line {exc.lineno}: {exc.msg}"
        if args.json:
            print(json.dumps({"errors": [{"msg": message}], "warnings": []}, indent=2))
        else:
            print(f"SYNTAX ERROR line {exc.lineno}: {exc.msg}")
        return 2
    except (OSError, RobotCapabilityError) as exc:
        message = f"Capability configuration error: {exc}"
        if args.json:
            print(json.dumps({"errors": [{"msg": message}], "warnings": []}, indent=2))
        else:
            print(message)
        return 2

    if args.json:
        print(json.dumps(_payload(errors, warnings), ensure_ascii=False, indent=2))
    else:
        for message in errors:
            print(f"ERROR   {message}")
        for message in warnings:
            print(f"WARNING {message}")
        print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
