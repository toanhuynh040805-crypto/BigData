"""Spark ingestion, cleaning, descriptive statistics and local dashboard exports."""
from __future__ import annotations

import json
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession, Window, functions as F

MEASUREMENTS = {
    "Global_active_power": "power_kw",
    "Global_reactive_power": "reactive_power_kw",
    "Voltage": "voltage_v",
    "Global_intensity": "current_a",
    "Sub_metering_1": "sub1_wh",
    "Sub_metering_2": "sub2_wh",
    "Sub_metering_3": "sub3_wh",
}


def make_spark(master: str = "local[*]") -> SparkSession:
    return (
        SparkSession.builder.appName("BigData-Energy-Consumption")
        .master(master)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.ansi.enabled", "false")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )


def read_raw(spark: SparkSession, path: str) -> DataFrame:
    frame = (
        spark.read.option("header", "true")
        .option("sep", ";")
        .option("inferSchema", "false")
        .csv(path)
    )
    missing = sorted(({"Date", "Time"} | set(MEASUREMENTS)) - set(frame.columns))
    if missing:
        raise ValueError(f"Dataset does not contain required columns: {missing}")
    return frame


def parse_records(frame: DataFrame) -> DataFrame:
    """Canonicalize d/M/yyyy into yyyy-MM-dd before parsing in fixed UTC Spark TZ.

    UTC is a neutral parser setting only; source readings are *local wall clock*
    with unknown offsets. Do NOT convert these timestamps to another zone.
    """
    pieces = F.split(F.trim(F.col("Date")), "/")
    iso_date = F.concat_ws(
        "-",
        F.lpad(pieces.getItem(2), 4, "0"),
        F.lpad(pieces.getItem(1), 2, "0"),
        F.lpad(pieces.getItem(0), 2, "0"),
    )
    result = frame.withColumn(
        "timestamp",
        F.to_timestamp(
            F.concat_ws(" ", iso_date, F.trim(F.col("Time"))),
            "yyyy-MM-dd HH:mm:ss",
        ),
    )
    for source, target in MEASUREMENTS.items():
        result = result.withColumn(
            target,
            F.when(
                F.trim(F.col(source)).isin("", "?"),
                F.lit(None),
            ).otherwise(F.col(source)).cast("double"),
        )
    return result.select("timestamp", *MEASUREMENTS.values())


def valid_records(parsed: DataFrame) -> DataFrame:
    return parsed.where(
        F.col("timestamp").isNotNull()
        & F.col("power_kw").isNotNull()
        & (~F.isnan("power_kw"))
        & (F.col("power_kw") >= 0)
    )


def clean_records(parsed: DataFrame) -> DataFrame:
    """Keep one deterministic, best-populated record per wall-clock minute."""
    valid = valid_records(parsed)
    measurements = list(MEASUREMENTS.values())
    quality_score = sum(
        (F.when(F.col(name).isNotNull() & (~F.isnan(name)), 1).otherwise(0)
         for name in measurements),
        F.lit(0),
    )
    result = valid.withColumn("_completeness", quality_score)
    rank = Window.partitionBy("timestamp").orderBy(
        F.col("_completeness").desc(),
        F.col("power_kw").asc(),
        F.col("voltage_v").asc_nulls_last(),
    )
    result = (
        result.withColumn("_rn", F.row_number().over(rank))
        .where(F.col("_rn") == 1)
        .drop("_rn", "_completeness")
    )
    for field in ("sub1_wh", "sub2_wh", "sub3_wh"):
        result = result.withColumn(
            field,
            F.when(
                F.col(field).isNotNull()
                & (~F.isnan(field))
                & (F.col(field) >= 0),
                F.col(field),
            ),
        )
    return (
        result.withColumn("date", F.to_date("timestamp"))
        .withColumn("hour", F.hour("timestamp"))
        .withColumn("year", F.year("timestamp"))
        .withColumn("month", F.month("timestamp"))
    )


def describe_quality(parsed: DataFrame, cleaned: DataFrame) -> dict:
    stats = parsed.agg(
        F.count("*").alias("raw_rows"),
        F.sum(F.when(F.col("timestamp").isNull(), 1).otherwise(0)).alias("bad_timestamp"),
        F.sum(F.when(F.col("power_kw").isNull() | F.isnan("power_kw"), 1).otherwise(0)).alias("missing_or_nan_power"),
        F.sum(F.when(F.col("power_kw") < 0, 1).otherwise(0)).alias("negative_power"),
    ).first().asDict()
    before_dedup = valid_records(parsed).count()
    kept = cleaned.count()
    return {
        **{key: int(value or 0) for key, value in stats.items()},
        "valid_before_dedup": int(before_dedup),
        "clean_unique_rows": int(kept),
        "invalid_rows": int(stats["raw_rows"] - before_dedup),
        "duplicates_removed": int(before_dedup - kept),
        "note": (
            "Duplicate local wall-clock timestamps are collapsed by completeness; "
            "timezone/DST offsets cannot be recovered from the original data."
        ),
    }


def aggregates(clean: DataFrame, expected_minutes_per_day: int = 1440) -> tuple[DataFrame, DataFrame, DataFrame]:
    if expected_minutes_per_day < 1:
        raise ValueError("expected_minutes_per_day must be positive")
    daily = (
        clean.groupBy("date")
        .agg(
            (F.sum("power_kw") / 60.0).alias("energy_kwh"),
            F.count("*").alias("valid_minutes"),
            (F.sum("sub1_wh") / 1000.0).alias("sub1_kwh"),
            (F.sum("sub2_wh") / 1000.0).alias("sub2_kwh"),
            (F.sum("sub3_wh") / 1000.0).alias("sub3_kwh"),
            F.avg("voltage_v").alias("mean_voltage_v"),
            F.avg("power_kw").alias("mean_power_kw"),
        )
        .withColumn(
            "coverage",
            F.least(F.lit(1.0), F.col("valid_minutes") / F.lit(float(expected_minutes_per_day))),
        )
    )
    monthly = (
        daily.withColumn("month", F.date_format("date", "yyyy-MM"))
        .groupBy("month")
        .agg(
            F.sum("energy_kwh").alias("energy_kwh"),
            F.avg("coverage").alias("mean_daily_coverage"),
            F.count("*").alias("observed_days"),
        )
        .orderBy("month")
    )
    hourly_profile = (
        clean.groupBy("hour")
        .agg(
            F.avg("power_kw").alias("mean_power_kw"),
            (F.sum("power_kw") / 60.0).alias("observed_energy_kwh"),
            F.count("*").alias("valid_minutes"),
        )
        .orderBy("hour")
    )
    return daily, monthly, hourly_profile


def export_aggregates(
    clean: DataFrame,
    daily: DataFrame,
    monthly: DataFrame,
    hourly_profile: DataFrame,
    output: Path,
    hdfs_parquet_output: str | None = None,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    # Spark honors Hadoop fs.defaultFS. Without an explicit file:// scheme,
    # a seemingly relative local path silently goes to HDFS when connected.
    local_parquet_uri = (output / "clean_parquet").resolve().as_uri()
    (clean.write.mode("overwrite")
        .partitionBy("year", "month")
        .parquet(local_parquet_uri))
    if hdfs_parquet_output:
        # Optional second write allows inspecting both source and processed
        # Parquet directly in HDFS, separate from local CSV/JSON dashboard data.
        (clean.write.mode("overwrite")
            .partitionBy("year", "month")
            .parquet(hdfs_parquet_output))
    for name, frame, order in (
        ("daily.csv", daily, "date"),
        ("monthly.csv", monthly, "month"),
        ("hourly_profile.csv", hourly_profile, "hour"),
    ):
        # Intentional: only reduced aggregates are collected to the driver.
        frame.orderBy(order).toPandas().to_csv(output / name, index=False)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
