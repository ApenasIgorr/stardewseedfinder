from __future__ import annotations

import argparse
import json
from pathlib import Path

from core.config import parse_json_or_yaml, parse_requirements
from core.search.engine import search_best


def main() -> None:
    parser = argparse.ArgumentParser(description="Stardew Seed Finder CLI")
    parser.add_argument("--config", required=True, help="Path to YAML/JSON config")
    parser.add_argument("--out", default="results.json", help="Output path (.json or .csv)")
    args = parser.parse_args()

    raw = Path(args.config).read_text()
    data = parse_json_or_yaml(raw)
    cfg = parse_requirements(data)
    results = search_best(cfg.model_dump())

    out_path = Path(args.out)
    if out_path.suffix.lower() == ".csv":
        lines = ["seed,score,hard_passed,unsupported"]
        for r in results:
            lines.append(f"{r['seed']},{r['score']},{r['hard_passed']},\"{';'.join(r['unsupported'])}\"")
        out_path.write_text("\n".join(lines))
    else:
        out_path.write_text(json.dumps(results, indent=2))

    print(f"Wrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    main()
