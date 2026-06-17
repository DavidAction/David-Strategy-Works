from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402
from hwpx_template_probe import analyze_hwpx_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy real government HWPX samples into the private local template library and probe them.")
    parser.add_argument("files", nargs="+", help="HWPX sample files downloaded from government grant notices.")
    args = parser.parse_args()

    server.ensure_dirs()
    sample_dir = server.TEMPLATE_DIR / "real_samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"samples": []}
    for item in args.files:
        source = Path(item).expanduser().resolve()
        if not source.exists() or source.suffix.lower() != ".hwpx":
            manifest["samples"].append({"source": str(source), "status": "skipped", "reason": "not_found_or_not_hwpx"})
            continue
        target = sample_dir / server.safe_filename(source.stem, "sample")
        target = target.with_suffix(".hwpx")
        shutil.copy2(source, target)
        analysis = analyze_hwpx_path(target)
        manifest["samples"].append({"source": str(source), "storedName": str(target.relative_to(server.TEMPLATE_DIR)), "status": "imported", "analysis": analysis})
    manifest_path = server.TEMPLATE_DIR / "hwpx-sample-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
