"""End-to-end Spark pipeline: clean -> Parquet -> aggregates -> forecast."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from energy_bigdata.model import train_and_forecast
from energy_bigdata.pipeline import (
    aggregates,
    clean_records,
    describe_quality,
    export_aggregates,
    make_spark,
    parse_records,
    read_raw,
    write_json,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/household_power_consumption.txt")
    parser.add_argument("--output", type=Path, default=Path("data/outputs"))
    parser.add_argument("--master", default="local[*]")
    parser.add_argument("--expected-minutes-per-day", type=int, default=1440)
    parser.add_argument("--min-coverage", type=float, default=0.9)
    parser.add_argument("--min-train-rows", type=int, default=60)
    parser.add_argument("--num-trees", type=int, default=60)
    parser.add_argument(
        "--data-provenance",
        choices=["uci", "synthetic", "other"],
        default="other",
        help="Set 'uci' for data obtained from UCI; 'synthetic' for offline fixture.",
    )
    args = parser.parse_args()
    if args.expected_minutes_per_day <= 0:
        parser.error("--expected-minutes-per-day must be positive")
    if not 0 < args.min_coverage <= 1:
        parser.error("--min-coverage must be between 0 (exclusive) and 1")
    if args.num_trees < 1 or args.min_train_rows < 10:
        parser.error("--num-trees >= 1 and --min-train-rows >= 10 required")
    if not args.input.startswith(("hdfs://", "s3a://", "file://")):
        if not Path(args.input).is_file():
            parser.error(f"Input does not exist: {args.input}. Run download_data.py first.")

    spark = make_spark(args.master)
    parsed = None
    clean = None
    try:
        raw = read_raw(spark, args.input)
        parsed = parse_records(raw).cache()
        clean = clean_records(parsed).cache()
        quality = describe_quality(parsed, clean)
        quality.update(
            {
                "data_provenance": args.data_provenance,
                "input_path": args.input,
                "energy_formula": "sum(power_kw)/60 for valid minute observations",
                "expected_minutes_per_day": args.expected_minutes_per_day,
            }
        )
        write_json(args.output / "quality.json", quality)
        print(f"Quality: {quality}")
        if quality["clean_unique_rows"] == 0:
            raise ValueError("No valid measurements remain after cleaning")

        daily, monthly, hourly = aggregates(clean, args.expected_minutes_per_day)
        export_aggregates(clean, daily, monthly, hourly, args.output)
        metrics = train_and_forecast(
            daily,
            args.output,
            min_coverage=args.min_coverage,
            min_train_rows=args.min_train_rows,
            num_trees=args.num_trees,
        )
        metrics["data_provenance"] = args.data_provenance
        write_json(args.output / "metrics.json", metrics)
        print(f"Model result: {metrics}")
        print(f"Results: {args.output.resolve()}")
    finally:
        if clean is not None:
            clean.unpersist()
        if parsed is not None:
            parsed.unpersist()
        spark.stop()


if __name__ == "__main__":
    main()
