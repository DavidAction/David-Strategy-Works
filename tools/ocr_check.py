from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def command_status(command: str) -> dict[str, object]:
    resolved = shutil.which(command) or (command if Path(command).exists() else "")
    return {"command": command, "available": bool(resolved), "resolved": resolved}


def analyze_file(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    text, notes = server.extract_text(path.name, data, "")
    return {
        "filename": path.name,
        "bytes": len(data),
        "extractedCharacters": len(text),
        "notes": notes,
        "preview": text[:500],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify OCR adapters and optionally test extraction on files.")
    parser.add_argument("--require-ocr", action="store_true", help="Exit with code 1 if Tesseract is unavailable.")
    parser.add_argument("files", nargs="*", help="Optional PDF/image files to test.")
    args = parser.parse_args()

    server.load_env_file()
    tesseract = os.environ.get("TESSERACT_CMD", "tesseract")
    pdftoppm = os.environ.get("PDFTOPPM_CMD", "pdftoppm")
    result = {
        "tesseract": command_status(tesseract),
        "pdftoppm": command_status(pdftoppm),
        "ocrLanguage": os.environ.get("OCR_LANG", "kor+eng"),
        "files": [],
    }
    for item in args.files:
        path = Path(item).expanduser().resolve()
        result["files"].append(analyze_file(path) if path.exists() else {"filename": item, "error": "not_found"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.require_ocr and not result["tesseract"]["available"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
