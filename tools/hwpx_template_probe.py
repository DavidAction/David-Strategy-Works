from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def analyze_hwpx_path(path: Path) -> dict[str, object]:
    section_files: list[str] = []
    table_count = 0
    cell_count = 0
    paragraph_count = 0
    text_nodes: list[str] = []
    placeholders: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".xml"):
                continue
            if not name.startswith("Contents/"):
                continue
            if "section" in name.lower():
                section_files.append(name)
            try:
                root = ET.fromstring(archive.read(name))
            except Exception:
                continue
            for element in root.iter():
                lname = server.local_xml_name(element.tag).lower()
                if lname in {"tbl", "table"}:
                    table_count += 1
                elif lname in {"tc", "cell"}:
                    cell_count += 1
                elif lname == "p":
                    paragraph_count += 1
                elif lname in {"t", "text"} and element.text and element.text.strip():
                    text = server.clean_text(element.text)
                    text_nodes.append(text)
                    placeholders.extend(re.findall(r"\{\{[^}]{1,80}\}\}|\[[^\]]{1,80}\]|__[^_]{1,80}__", text))
    return {
        "filename": path.name,
        "sectionXmlCount": len(section_files),
        "sectionFiles": section_files[:20],
        "tableCount": table_count,
        "cellCount": cell_count,
        "paragraphCount": paragraph_count,
        "textNodeCount": len(text_nodes),
        "placeholderCount": len(placeholders),
        "placeholders": placeholders[:80],
        "fillMode": "cell_level_candidate" if cell_count else ("paragraph_level_candidate" if paragraph_count else "appendix_only"),
        "sampleText": " ".join(text_nodes[:120])[:1600],
        "recommendedTokens": ["{{answer_1}}", "{q1}", "[답변1]", "__ANSWER_1__"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe government HWPX templates for cell/placeholder fill readiness.")
    parser.add_argument("files", nargs="*", help="HWPX files. If omitted, probes data/templates/*.hwpx.")
    args = parser.parse_args()

    paths = [Path(item).expanduser().resolve() for item in args.files]
    if not paths:
        paths = sorted((ROOT / "data" / "templates").glob("*.hwpx"))
    result = {"templates": []}
    for path in paths:
        if not path.exists():
            result["templates"].append({"filename": str(path), "error": "not_found"})
            continue
        if path.suffix.lower() != ".hwpx":
            result["templates"].append({"filename": str(path), "error": "not_hwpx"})
            continue
        try:
            result["templates"].append(analyze_hwpx_path(path))
        except Exception as exc:
            result["templates"].append({"filename": path.name, "error": str(exc)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
