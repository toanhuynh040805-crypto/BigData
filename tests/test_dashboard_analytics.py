"""Unit tests for dashboard computations (no Spark or Streamlit needed)."""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from dashboard.analytics import (
    anomalies_iqr,
    calendar_rolling,
    csv_bytes,
    device_totals,
    distribution_by_weekday,
    monthly_from_daily,
    prepare_daily,
    prepare_predictions,
    select_daily,
)


def fixture_daily(days: int = 30) -> pd.DataFrame:
    dates = pd.date_range("2010-01-01", periods=days, freq="D")
    return prepare_daily(
        pd.DataFrame({
            "date": dates.astype(str),
            "energy_kwh": [20.0] * days,
            "coverage": [1.0] * days,
            "valid_minutes": [1440] * days,
            "sub1_kwh": [4.0] * days,
            "sub2_kwh": [2.0] * days,
            "sub3_kwh": [3.0] * days,
        })
    )


def test_filter_and_monthly_totals_not_global():
    df = fixture_daily(40)
    selected = select_daily(df, date(2010, 1, 10), date(2010, 1, 14))
    month = monthly_from_daily(selected)
    assert len(selected) == 5
    assert month.iloc[0]["energy_kwh"] == pytest.approx(100.0)
    assert month.iloc[0]["observed_days"] == 5


def test_rolling_rejects_missing_calendar_days():
    df = fixture_daily(10)
    df = df[df["date"].dt.day != 5].copy()
    rolled = calendar_rolling(df, window=3)
    assert pd.isna(rolled.loc[rolled["date"].dt.day == 6, "rolling_kwh"].iloc[0])
    assert rolled.loc[rolled["date"].dt.day == 10, "rolling_kwh"].iloc[0] == pytest.approx(20.0)


def test_device_totals_do_not_double_count():
    df = fixture_daily(2)
    items = device_totals(df)
    assert items["energy_kwh"].sum() == pytest.approx(40.0)
    assert "Chưa phân nhánh" in items["device"].tolist()


def test_outlier_excludes_partial_days():
    df = fixture_daily(40)
    df.loc[df.index[0], "energy_kwh"] = 90.0
    df.loc[df.index[1], "energy_kwh"] = 0.2
    df.loc[df.index[1], "coverage"] = 0.2
    unusual, info = anomalies_iqr(df)
    assert info["status"] == "ok"
    assert len(unusual) == 1
    assert unusual.iloc[0]["type"] == "Cao bất thường"


def test_weekday_names_and_excel_export():
    df = fixture_daily(10)
    assert distribution_by_weekday(df)["days"].sum() == 10
    assert csv_bytes(df).startswith(b"\xef\xbb\xbf")


def test_prediction_errors():
    df = pd.DataFrame({
        "date": ["2010-01-01", "2010-01-02"],
        "actual_kwh": [10, 20],
        "rf_prediction_kwh": [11, 19],
        "baseline_kwh": [13, 16],
    })
    result = prepare_predictions(df)
    assert result["abs_error_kwh"].tolist() == [1, 1]
    assert result["baseline_abs_error_kwh"].tolist() == [3, 4]


def test_bad_daily_input_fails_loudly():
    with pytest.raises(ValueError):
        prepare_daily(pd.DataFrame({"date": ["2010-01-01"]}))
