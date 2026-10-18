#!/usr/bin/env python3
"""Write or verify the committed public API contract deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from davdeploy.main import app

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "openapi-v1.json"


def rendered_contract() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    rendered = rendered_contract()
    if args.write:
        CONTRACT.parent.mkdir(parents=True, exist_ok=True)
        CONTRACT.write_text(rendered)
        print(f"Wrote {CONTRACT.relative_to(ROOT)}")
        return 0
    if not CONTRACT.exists() or CONTRACT.read_text() != rendered:
        print("OpenAPI snapshot differs; run: make openapi-update")
        return 1
    print("OpenAPI v1 snapshot matches the FastAPI application.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

