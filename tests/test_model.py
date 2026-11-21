"""Forecasting must never use day-D label as a feature or skip missing days."""
from __future__ import annotations

from datetime import date, timedelta

import pytest


def test_calendar_lags_and_future_row(spark):
    from energy_bigdata.model import make_features

    first = date(2008, 1, 1)
    rows = [(first + timedelta(days=i), float(10 + i), 1.0) for i in range(14)]
    daily = spark.createDataFrame(rows, "date date, energy_kwh double, coverage double")
    features = make_features(daily)
    day8 = features.where("date = '2008-01-08'").first()
    assert day8["lag_1_kwh"] == pytest.approx(16.0)
    assert day8["lag_7_kwh"] == pytest.approx(10.0)
    assert day8["rolling_7d_kwh"] == pytest.approx(13.0)
    assert day8["target_kwh"] == pytest.approx(17.0)
    future = features.where("date = '2008-01-15'").first()
    assert future["target_kwh"] is None
    assert future["lag_1_kwh"] == pytest.approx(23.0)


def test_missing_calendar_day_does_not_become_previous_day(spark):
    from energy_bigdata.model import make_features

    daily = spark.createDataFrame(
        [
            (date(2008, 1, 1), 10.0, 1.0),
            (date(2008, 1, 3), 20.0, 1.0),
        ],
        "date date, energy_kwh double, coverage double",
    )
    jan3 = make_features(daily).where("date = '2008-01-03'").first()
    assert jan3["lag_1_kwh"] is None


def test_min_coverage_suppresses_incomplete_day(spark):
    from energy_bigdata.model import make_features

    daily = spark.createDataFrame(
        [
            (date(2008, 1, 1), 10.0, 0.25),
            (date(2008, 1, 2), 20.0, 1.0),
        ],
        "date date, energy_kwh double, coverage double",
    )
    jan2 = make_features(daily).where("date = '2008-01-02'").first()
    assert jan2["lag_1_kwh"] is None
