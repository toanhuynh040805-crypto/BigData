"""OPSD hourly national electricity loads are NOT UCI household readings."""
from __future__ import annotations
import json
from pathlib import Path
from pyspark.sql import DataFrame, functions as F

OPSD_URL = "https://data.open-power-system-data.org/time_series/2020-10-06/time_series_60min_singleindex.csv"
OPSD_DOI = "https://doi.org/10.25832/time_series/2020-10-06"
COUNTRIES = {
    "DE": ("Đức", "DE_load_actual_entsoe_transparency"),
    "FR": ("Pháp", "FR_load_actual_entsoe_transparency"),
    "IT": ("Ý", "IT_load_actual_entsoe_transparency"),
    "ES": ("Tây Ban Nha", "ES_load_actual_entsoe_transparency"),
    "GB": ("Great Britain", "GB_GBN_load_actual_entsoe_transparency"),
}
ISO3 = {"DE": "DEU", "FR": "FRA", "IT": "ITA", "ES": "ESP", "GB": "GBR"}


def hourly_load(source: DataFrame, year: int = 2019) -> DataFrame:
    """Use actual measured MW. Missing/negative measurements are never imputed."""
    required = {"utc_timestamp"} | {col for _, col in COUNTRIES.values()}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"OPSD 60-minute file is missing columns: {sorted(missing)}")
    if year < 2015 or year > 2020:
        raise ValueError("The OPSD release spans 2015–2020.")

    stamp = F.to_timestamp(F.trim(F.col("utc_timestamp")), "yyyy-MM-dd'T'HH:mm:ss'Z'")
    selected = source.withColumn("timestamp_utc", stamp).where(
        F.col("timestamp_utc").isNotNull() & (F.year("timestamp_utc") == year)
    )
    long = selected.select(
        "timestamp_utc",
        F.explode(F.array(*[
            F.struct(
                F.lit(code).alias("country"),
                F.lit(name).alias("country_name"),
                F.lit(ISO3[code]).alias("iso3"),
                F.col(field).cast("double").alias("load_mw"),
            )
            for code, (name, field) in COUNTRIES.items()
        ])).alias("reading"),
    ).select("timestamp_utc", "reading.*")
    valid = long.where(
        F.col("load_mw").isNotNull() & (~F.isnan("load_mw")) & (F.col("load_mw") >= 0)
    )
    # Repeated UTC hours should not be counted twice.
    return (
        valid.groupBy("timestamp_utc", "country", "country_name", "iso3")
        .agg(F.avg("load_mw").alias("load_mw"))
        .withColumn("date", F.to_date("timestamp_utc"))
        .withColumn("hour_utc", F.hour("timestamp_utc"))
    )


def regional_aggregates(hourly: DataFrame) -> tuple[DataFrame, DataFrame, DataFrame]:
    """GWh over observed hours = sum(hourly average MW * 1h) / 1000."""
    daily = (
        hourly.groupBy("country", "country_name", "iso3", "date")
        .agg(
            (F.sum("load_mw") / 1000.0).alias("observed_gwh"),
            F.count("*").alias("observed_hours"),
            F.avg("load_mw").alias("mean_load_mw"),
            F.max("load_mw").alias("peak_load_mw"),
        )
        .withColumn("coverage", F.least(F.lit(1.0), F.col("observed_hours") / 24.0))
    )
    monthly = (
        daily.withColumn("month", F.date_format("date", "yyyy-MM"))
        .groupBy("country", "country_name", "iso3", "month")
        .agg(
            F.sum("observed_gwh").alias("observed_gwh"),
            F.avg("coverage").alias("mean_daily_coverage"),
            F.count("*").alias("observed_days"),
            F.sum("observed_hours").alias("observed_hours"),
        )
    )
    profile = (
        hourly.groupBy("country", "country_name", "iso3", "hour_utc")
        .agg(F.avg("load_mw").alias("mean_load_mw"), F.count("*").alias("observed_hours"))
    )
    return daily, monthly, profile


def publish_regions(
    daily: DataFrame, monthly: DataFrame, profile: DataFrame,
    destination: Path, year: int,
) -> dict:
    """Store only compact Spark aggregates locally."""
    destination.mkdir(parents=True, exist_ok=True)
    for name, frame, columns in (
        ("daily.csv", daily, ["country", "date"]),
        ("monthly.csv", monthly, ["country", "month"]),
        ("hourly_profile.csv", profile, ["country", "hour_utc"]),
    ):
        frame.orderBy(*columns).toPandas().to_csv(destination / name, index=False)
    rows = (
        daily.groupBy("country", "country_name")
        .agg(
            F.count("*").alias("observed_days"),
            F.sum("observed_hours").alias("observed_hours"),
            F.avg("coverage").alias("mean_daily_coverage"),
            F.sum(F.when(F.col("coverage") == 1, 1).otherwise(0)).alias("complete_days"),
        ).orderBy("country").collect()
    )
    quality = {
        "source": "Open Power System Data (OPSD), Time series 2020-10-06",
        "source_url": OPSD_URL, "doi": OPSD_DOI, "provenance": "opsd",
        "data_kind": "national grid hourly load, not household consumption",
        "year": year, "timezone": "UTC",
        "unit": {"hourly": "MW", "daily": "GWh", "monthly": "GWh"},
        "aggregation": "sum of 1-hour MW measurements / 1000 = GWh",
        "countries": {
            r["country"]: {
                "name": r["country_name"],
                "observed_days": int(r["observed_days"]),
                "observed_hours": int(r["observed_hours"]),
                "mean_daily_coverage": float(r["mean_daily_coverage"]),
                "complete_days": int(r["complete_days"]),
            } for r in rows
        },
        "caveats": [
            "Country totals are not population-normalized.",
            "Missing hours remain unfilled and can lower totals.",
            "National GWh values must not be compared to UCI household kWh.",
            "OPSD 2019 and UCI 2006–2010 are separate independent datasets.",
        ],
    }
    (destination / "quality.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return quality
