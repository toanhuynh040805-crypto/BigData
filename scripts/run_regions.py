"""Run the supplementary national-level OPSD Spark analysis (not UCI model)."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from energy_bigdata.pipeline import make_spark
from energy_bigdata.regions import COUNTRIES, hourly_load, publish_regions, regional_aggregates

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", default="data/raw/time_series_60min_singleindex.csv")
    p.add_argument("--output", type=Path, default=Path("data/outputs/regions"))
    p.add_argument("--year", type=int, default=2019)
    p.add_argument("--master", default="local[2]")
    args = p.parse_args()
    if not args.input.startswith(("hdfs://", "s3a://", "file://")) and not Path(args.input).is_file():
        p.error("OPSD file not found. Run scripts/download_regions.py first.")
    spark = make_spark(args.master)
    try:
        source = spark.read.option("header", "true").option("inferSchema", "false").csv(args.input)
        hourly = hourly_load(source, args.year).cache()
        if not hourly.take(1):
            raise ValueError("No OPSD observations for selected year")
        daily, monthly, profile = regional_aggregates(hourly)
        quality = publish_regions(daily, monthly, profile, args.output, args.year)
        missing = set(COUNTRIES) - set(quality["countries"])
        if missing:
            raise ValueError(f"Missing observations for countries: {sorted(missing)}")
        print("OPSD countries:", quality["countries"])
        print("Results:", args.output.resolve())
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
