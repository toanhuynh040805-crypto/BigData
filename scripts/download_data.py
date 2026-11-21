"""Download the original UCI Household Electric Power Consumption dataset.

Source: https://doi.org/10.24432/C58K54 (CC BY 4.0).
No credentials required. Dataset archive is ~20 MB; extracted TXT ~127 MB.
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

UCI_ZIP_URL = (
    "https://archive.ics.uci.edu/static/public/235/"
    "individual+household+electric+power+consumption.zip"
)
DEFAULT_DEST = Path("data/raw/household_power_consumption.txt")
MEMBER_NAME = "household_power_consumption.txt"


def extract_dataset(archive: Path, destination: Path) -> Path:
    """Extract only the expected dataset member (no arbitrary ZIP paths)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        matches = [
            member for member in source.namelist()
            if Path(member).name == MEMBER_NAME and not member.endswith("/")
        ]
        if len(matches) != 1:
            raise ValueError("Archive must contain exactly one household_power_consumption.txt")
        with source.open(matches[0]) as infile, destination.open("wb") as outfile:
            shutil.copyfileobj(infile, outfile)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--url", default=UCI_ZIP_URL, help="Optional trusted mirror ZIP URL")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing TXT")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        print(f"Already present: {args.output} (add --force to replace)")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bigdata-uci-") as directory:
        archive = Path(directory) / "source.zip"
        print(f"Downloading UCI dataset from {args.url}")
        urllib.request.urlretrieve(args.url, archive)
        result = extract_dataset(archive, args.output)
    print(f"Extracted {result} ({result.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
