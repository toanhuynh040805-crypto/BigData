"""Fetch OPSD national-grid hourly data, published in its 2020-10-06 release."""
from __future__ import annotations
import argparse
import shutil
import urllib.request
from pathlib import Path

SOURCE = "https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv"
DEST = Path("data/raw/time_series_60min_singleindex.csv")

def download(path: Path, url: str = SOURCE, force: bool = False) -> Path:
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(".partial")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "BigDataEnergyStudent/1.0"})
        with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as output:
            shutil.copyfileobj(response, output, length=2 * 1024 * 1024)
        with partial.open("rb") as check:
            if not check.read(25).startswith(b"utc_timestamp"):
                raise ValueError("File downloaded does not look like an OPSD hourly CSV")
        partial.replace(path)
        return path
    finally:
        if partial.exists():
            partial.unlink()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=DEST)
    p.add_argument("--url", default=SOURCE)
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    path = download(args.output, args.url, args.force)
    print(f"OPSD: {path} ({path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
