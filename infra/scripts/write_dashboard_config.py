import json
import os
import pathlib
import sys


def main() -> None:
    out = (os.environ.get("OUT_PATH") or "").strip()
    url = (os.environ.get("DASHBOARD_WS_URL") or "").strip()
    tok = (os.environ.get("DASHBOARD_WRITE_TOKEN") or "").strip()
    if not out or not url or not tok:
        print(
            "Set OUT_PATH, DASHBOARD_WS_URL, DASHBOARD_WRITE_TOKEN (run 33-write-dashboard-config.sh).",
            file=sys.stderr,
        )
        sys.exit(1)
    p = pathlib.Path(out)
    obj = {"wsUrl": url, "token": tok}
    body = json.dumps(obj, ensure_ascii=False, indent=2)
    p.write_text(
        f"window.__DASHBOARD_CONFIG__ = {body};\n",
        encoding="utf-8",
    )
    print(f"Wrote {p}")


if __name__ == "__main__":
    main()
