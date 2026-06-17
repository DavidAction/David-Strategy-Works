from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


COMMON_TESSERACT_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\tools\tesseract\tesseract.exe"),
]

COMMON_PDFTOPPM_PATHS = [
    Path(r"C:\ProgramData\chocolatey\bin\pdftoppm.exe"),
    Path(r"C:\tools\poppler\bin\pdftoppm.exe"),
    Path(r"C:\Program Files\poppler\Library\bin\pdftoppm.exe"),
    Path(r"C:\Program Files\poppler\bin\pdftoppm.exe"),
]


def resolve_command(command: str, common_paths: list[Path]) -> str:
    resolved = shutil.which(command)
    if resolved:
        return resolved
    path = Path(command)
    if path.exists():
        return str(path)
    for candidate in common_paths:
        if candidate.exists():
            return str(candidate)
    return ""


def command_status(command: str) -> dict[str, object]:
    common = COMMON_TESSERACT_PATHS if "tesseract" in command.lower() else COMMON_PDFTOPPM_PATHS
    resolved = resolve_command(command, common)
    return {"command": command, "available": bool(resolved), "resolved": resolved}


def tesseract_languages(tesseract_path: str) -> list[str]:
    if not tesseract_path:
        return []
    try:
        result = subprocess.run([tesseract_path, "--list-langs"], capture_output=True, text=True, timeout=20)
    except Exception:
        return []
    lines = [line.strip() for line in (result.stdout or result.stderr).splitlines() if line.strip()]
    return [line for line in lines if not line.lower().startswith("list of")]


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
    result["tesseract"]["languages"] = tesseract_languages(str(result["tesseract"].get("resolved") or ""))
    result["koreanReady"] = "kor" in result["tesseract"].get("languages", [])
    result["pdfOcrReady"] = bool(result["tesseract"]["available"] and result["pdftoppm"]["available"])
    for item in args.files:
        path = Path(item).expanduser().resolve()
        result["files"].append(analyze_file(path) if path.exists() else {"filename": item, "error": "not_found"})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if args.require_ocr and not result["tesseract"]["available"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
