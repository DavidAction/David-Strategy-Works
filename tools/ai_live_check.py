from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live Gemini/OpenAI/Anthropic connectivity checks.")
    parser.add_argument("--no-live", action="store_true", help="Only report configured API keys without calling providers.")
    args = parser.parse_args()

    server.load_env_file()
    result = server.ai_provider_health(live=not args.no_live)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if any(item.get("status") == "error" for item in result.get("checks", [])):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
