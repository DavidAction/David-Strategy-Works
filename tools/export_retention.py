from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or clean generated export files.")
    parser.add_argument("--days", type=int, default=None, help="Override retention age in days.")
    parser.add_argument("--delete", action="store_true", help="Delete files older than the retention age.")
    parser.add_argument("--confirm", default="", help="Required value DELETE_EXPORTS when using --delete.")
    args = parser.parse_args()

    server.load_env_file()
    if args.delete and args.confirm != "DELETE_EXPORTS":
        print("Refusing to delete. Pass --confirm DELETE_EXPORTS.", file=sys.stderr)
        return 2
    if args.delete:
        result = server.cleanup_exports(older_than_days=args.days, dry_run=False)
    else:
        result = server.export_retention_report(older_than_days=args.days)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
