from __future__ import annotations

import argparse
import json
import sys

from src import auto_convert_address, convert_csv_file

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
    parser.add_argument(
        "--input-csv",
        help="Path to an input CSV file for batch conversion.",
    )
    parser.add_argument(
        "--output-csv",
        help="Path to the output CSV file for batch conversion.",
    )
    parser.add_argument(
        "--address-column",
        default="full_address",
        help="CSV column containing the address text.",
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=4096,
        help="Maximum number of recent address conversions to keep in memory.",
    )
    return parser.parse_args()


def main() -> None:
    """Convert an address from CLI input and print the JSON result."""
    args = parse_args()
    if args.input_csv:
        if not args.output_csv:
            raise SystemExit("--output-csv is required when --input-csv is used.")
        written = convert_csv_file(
            args.input_csv,
            args.output_csv,
            address_column=args.address_column,
            cache_size=args.cache_size,
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "input_csv": args.input_csv,
                    "output_csv": args.output_csv,
                    "address_column": args.address_column,
                    "cache_size": args.cache_size,
                    "rows_written": written,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = auto_convert_address(args.address)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
