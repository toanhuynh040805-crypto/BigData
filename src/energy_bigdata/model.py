"""Chronological next-day load forecasting with Spark MLlib."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.sql import DataFrame, Window, functions as F

FEATURES = (
    "lag_1_kwh",
    "lag_7_kwh",
    "rolling_7d_kwh",
    "day_of_week",
    "month",
    "day_of_year",
)


def make_features(daily: DataFrame, min_coverage: float = 0.9) -> DataFrame:
    """Include *missing calendar dates* before lag/rolling calculations.

    Prediction target for day D is energy on D. All signals refer to D-1 or
    earlier, preventing same-day data leakage.
    """
    if not (0.0 < min_coverage <= 1.0):
        raise ValueError("min_coverage must be in (0, 1]")
    bounds = daily.agg(F.min("date").alias("first"), F.max("date").alias("last")).first()
    if not bounds or bounds["first"] is None:
        raise ValueError("There are no valid daily observations")
    calendar = daily.sparkSession.range(1).select(
        F.explode(
            F.sequence(F.lit(bounds["first"]), F.date_add(F.lit(bounds["last"]), 1))
        ).alias("date")
    )
    complete = (
        calendar.join(daily.select("date", "energy_kwh", "coverage"), on="date", how="left")
        .withColumn(
            "target_kwh",
            F.when(F.col("coverage") >= F.lit(min_coverage), F.col("energy_kwh")),
        )
    )
    ordered = Window.orderBy("date")
    trailing = ordered.rowsBetween(-7, -1)
    return (
        complete.withColumn("lag_1_kwh", F.lag("target_kwh", 1).over(ordered))
        .withColumn("lag_7_kwh", F.lag("target_kwh", 7).over(ordered))
        .withColumn("rolling_7d_kwh", F.avg("target_kwh").over(trailing))
        .withColumn("previous_days", F.count("target_kwh").over(trailing))
        .withColumn("day_of_week", F.dayofweek("date").cast("double"))
        .withColumn("month", F.month("date").cast("double"))
        .withColumn("day_of_year", F.dayofyear("date").cast("double"))
    )


def _metrics(frame: DataFrame) -> dict[str, float]:
    evaluator = RegressionEvaluator(labelCol="target_kwh", predictionCol="prediction")
    values: dict[str, float] = {}
    for name in ("mae", "rmse", "r2"):
        value = float(evaluator.setMetricName(name).evaluate(frame))
        values[name] = value if math.isfinite(value) else None
    return values


def train_and_forecast(
    daily: DataFrame,
    output: Path,
    min_coverage: float = 0.9,
    min_train_rows: int = 60,
    num_trees: int = 60,
) -> dict:
    """Hold out latest 20% of eligible days; save model and CSV score artifacts."""
    output.mkdir(parents=True, exist_ok=True)
    frame = make_features(daily, min_coverage)
    all_present = F.lit(True)
    for feature in FEATURES:
        all_present = all_present & F.col(feature).isNotNull()
    usable = frame.where(all_present & (F.col("previous_days") == 7))
    labeled = usable.where(F.col("target_kwh").isNotNull()).cache()
    total = labeled.count()
    if total < min_train_rows or total < 10:
        result = {
            "status": "insufficient_data",
            "eligible_days": total,
            "min_train_rows": min_train_rows,
            "message": "Need sufficient contiguous, high-coverage days for leakage-free evaluation.",
        }
        pd.DataFrame(columns=["date", "actual_kwh", "rf_prediction_kwh", "baseline_kwh"]).to_csv(
            output / "predictions.csv", index=False
        )
        pd.DataFrame(columns=["date", "predicted_kwh", "baseline_kwh"]).to_csv(
            output / "forecast.csv", index=False
        )
        labeled.unpersist()
        return result

    indexed = labeled.withColumn("_row", F.row_number().over(Window.orderBy("date")))
    cutoff = max(1, int(total * 0.8))
    assembler = VectorAssembler(inputCols=list(FEATURES), outputCol="features")
    train = assembler.transform(indexed.where(F.col("_row") <= cutoff))
    test = assembler.transform(indexed.where(F.col("_row") > cutoff))
    rf = RandomForestRegressor(
        featuresCol="features",
        labelCol="target_kwh",
        predictionCol="prediction",
        seed=42,
        numTrees=num_trees,
        maxDepth=8,
        maxBins=32,
    )
    model = rf.fit(train)
    predictions = model.transform(test).select(
        "date", "target_kwh", "prediction", "lag_1_kwh"
    ).cache()
    rf_metrics = _metrics(predictions)
    baseline_metrics = _metrics(
        predictions.select(
            "target_kwh", F.col("lag_1_kwh").alias("prediction")
        )
    )
    predicted_pdf = predictions.orderBy("date").toPandas().rename(
        columns={
            "target_kwh": "actual_kwh",
            "prediction": "rf_prediction_kwh",
            "lag_1_kwh": "baseline_kwh",
        }
    )
    predicted_pdf.to_csv(output / "predictions.csv", index=False)
    predictions.unpersist()

    # Retrain on all eligible historical observations for the next recorded day.
    full_model = rf.fit(assembler.transform(labeled))
    full_model.write().overwrite().save(str(output / "rf_model"))
    future = usable.where(F.col("target_kwh").isNull()).orderBy(F.col("date").desc()).limit(1)
    forecast = full_model.transform(assembler.transform(future)).select(
        "date", F.col("prediction").alias("predicted_kwh"),
        F.col("lag_1_kwh").alias("baseline_kwh"),
    )
    future_pdf = forecast.toPandas()
    future_pdf.to_csv(output / "forecast.csv", index=False)
    test_bounds = test.agg(
        F.min("date").alias("test_start"),
        F.max("date").alias("test_end"),
    ).first()

    metrics = {
        "status": "trained",
        "evaluation": "chronological 80/20 holdout, one-step-ahead",
        "target_unit": "kWh/day",
        "days_used": total,
        "train_rows": cutoff,
        "test_rows": total - cutoff,
        "test_start": str(test_bounds["test_start"]),
        "test_end": str(test_bounds["test_end"]),
        "min_coverage": min_coverage,
        "features": list(FEATURES),
        "random_forest": rf_metrics,
        "baseline_previous_day": baseline_metrics,
        "next_day_forecast_available": not future_pdf.empty,
        "forecast_date": str(future_pdf.iloc[0]["date"]) if not future_pdf.empty else None,
    }
    labeled.unpersist()
    return metrics
