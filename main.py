from __future__ import annotations

import argparse
import json
import sys

from src import auto_convert_address

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_ADDRESS = (
    "Sun Ponte Residence Đà Nẵng, "
    "Đường Trần Hưng Đạo, "
    "Phường An Hải Nam, "
    "Quận Sơn Trà, "
    "Đà Nẵng"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for address conversion."""
    parser = argparse.ArgumentParser(
        description="Convert a Vietnamese administrative address.",
    )
    parser.add_argument(
        "--address",
        nargs="?",
        const="",
        default=DEFAULT_ADDRESS,
        help="Address text to parse and convert.",
    )
    return parser.parse_args()


def main() -> None:
    """Convert an address from CLI input and print the JSON result."""
    args = parse_args()
    result = auto_convert_address(args.address)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
