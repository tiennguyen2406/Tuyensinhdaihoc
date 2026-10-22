"""Read-only HTTP acceptance check for a new, empty Docker installation."""

import argparse
import json
from urllib.request import urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--web", default="http://127.0.0.1:3000")
    args = parser.parse_args()
    for origin, path, empty in (
        (args.api, "/health/live", False),
        (args.api, "/health/ready", False),
        (args.api, "/api/v1/programs?year=2024&limit=20", True),
        (args.web, "/api/catalog/programs?year=2024&limit=20", True),
        (args.web, "/majors?year=2024", False),
    ):
        with urlopen(origin.rstrip("/") + path, timeout=15) as response:
            if response.status != 200:
                raise SystemExit("HTTP acceptance failed: " + path)
            body = response.read()
        if empty and json.loads(body).get("items") != []:
            raise SystemExit("Expected a new empty catalog: " + path)
        print("PASS", path)


if __name__ == "__main__":
    main()
