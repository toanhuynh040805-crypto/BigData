"""Pure, testable analytics over Spark's published *aggregated* outputs.

This layer deliberately avoids Spark and Streamlit: the dashboard can run on
Windows with only pandas, Plotly, and Streamlit installed.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

DAY_NAMES = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
MONTH_NAMES = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12"]
DEVICE_LABELS = {
    "sub1_kwh": "Bếp",
    "sub2_kwh": "Giặt & thiết bị phụ",
    "sub3_kwh": "Nước nóng & điều hòa",
}
DAILY_COLUMNS = {"date", "energy_kwh", "coverage", "valid_minutes", *DEVICE_LABELS}


def prepare_daily(source: pd.DataFrame) -> pd.DataFrame:
    """Parse dates and numeric units without silently fabricating measurements."""
    missing = DAILY_COLUMNS - set(source.columns)
    if missing:
        raise ValueError("daily.csv thiếu cột: " + ", ".join(sorted(missing)))
    result = source.copy()
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    for column in (DAILY_COLUMNS - {"date"}):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(subset=["date", "energy_kwh", "coverage"])
    result = result[result["energy_kwh"] >= 0]
    result = result.drop_duplicates(subset="date", keep="first").sort_values("date")
    result = result.reset_index(drop=True)
    result["weekday"] = result["date"].dt.weekday
    result["weekday_name"] = result["weekday"].map(dict(enumerate(DAY_NAMES)))
    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month
    return result


def select_daily(
    frame: pd.DataFrame,
    start: date,
    end: date,
    minimum_coverage: float = 0.0,
) -> pd.DataFrame:
    if start > end:
        raise ValueError("Ngày bắt đầu không thể sau ngày kết thúc.")
    if not 0 <= minimum_coverage <= 1:
        raise ValueError("Độ bao phủ phải nằm trong [0, 1].")
    mask = (
        frame["date"].dt.date.between(start, end)
        & (frame["coverage"] >= minimum_coverage)
    )
    return frame.loc[mask].copy()


def monthly_from_daily(frame: pd.DataFrame) -> pd.DataFrame:
    """Recompute monthly statistics from selected days; never show unfiltered totals."""
    if frame.empty:
        return pd.DataFrame(columns=["month", "energy_kwh", "coverage", "observed_days"])
    f = frame.assign(period=frame["date"].dt.to_period("M"))
    return (
        f.groupby("period", observed=True)
        .agg(
            energy_kwh=("energy_kwh", "sum"),
            coverage=("coverage", "mean"),
            observed_days=("date", "size"),
        )
        .reset_index()
        .assign(month=lambda d: d["period"].astype(str))
        .drop(columns="period")
    )


def calendar_rolling(frame: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Rolling mean over *calendar* days, not merely the previous N observed rows."""
    if not 2 <= window <= 365:
        raise ValueError("window must be between 2 and 365 days")
    if frame.empty:
        result = frame.copy()
        result["rolling_kwh"] = pd.Series(dtype=float)
        return result
    work = frame.set_index("date")["energy_kwh"].asfreq("D")
    smooth = work.rolling(window=window, min_periods=window).mean()
    result = frame.copy()
    result["rolling_kwh"] = result["date"].map(smooth)
    return result


def device_totals(frame: pd.DataFrame) -> pd.DataFrame:
    measured = {
        DEVICE_LABELS[key]: float(frame[key].fillna(0).sum())
        for key in DEVICE_LABELS
    }
    total = float(frame["energy_kwh"].sum())
    known = sum(measured.values())
    # Do not invent a negative "other" meter reading when measurements disagree.
    if total > known:
        measured["Chưa phân nhánh"] = total - known
    return pd.DataFrame(
        [{"device": name, "energy_kwh": value} for name, value in measured.items()]
    )


def distribution_by_weekday(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["weekday", "day", "mean_kwh", "days"])
    aggregate = (
        frame.groupby("weekday", observed=True)
        .agg(mean_kwh=("energy_kwh", "mean"), days=("energy_kwh", "size"))
        .reset_index()
        .sort_values("weekday")
    )
    aggregate["day"] = aggregate["weekday"].map(dict(enumerate(DAY_NAMES)))
    return aggregate


def anomalies_iqr(frame: pd.DataFrame, coverage_floor: float = 0.9) -> tuple[pd.DataFrame, dict]:
    """Flag statistical outliers, not equipment failures.

    Exclude incomplete days to avoid interpreting missing measurements as
    suspiciously low consumption. IQR requires >= 20 comparable days.
    """
    eligible = frame.loc[(frame["coverage"] >= coverage_floor) & frame["energy_kwh"].notna()].copy()
    if len(eligible) < 20:
        return eligible.iloc[:0].copy(), {"status": "insufficient_data", "sample": len(eligible)}
    q1, q3 = eligible["energy_kwh"].quantile([0.25, 0.75])
    iqr = float(q3 - q1)
    lower, upper = max(0.0, float(q1 - 1.5 * iqr)), float(q3 + 1.5 * iqr)
    unusual = eligible.loc[
        (eligible["energy_kwh"] < lower) | (eligible["energy_kwh"] > upper)
    ].copy()
    unusual["type"] = np.where(unusual["energy_kwh"] > upper, "Cao bất thường", "Thấp bất thường")
    return unusual.sort_values("date", ascending=False), {
        "status": "ok", "sample": len(eligible), "lower": lower, "upper": upper,
    }


def prepare_predictions(source: pd.DataFrame) -> pd.DataFrame:
    needed = {"date", "actual_kwh", "rf_prediction_kwh", "baseline_kwh"}
    missing = needed - set(source.columns)
    if missing:
        raise ValueError("predictions.csv thiếu cột: " + ", ".join(sorted(missing)))
    frame = source.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for name in needed - {"date"}:
        frame[name] = pd.to_numeric(frame[name], errors="coerce")
    frame = frame.dropna(subset=list(needed)).sort_values("date")
    frame["error_kwh"] = frame["rf_prediction_kwh"] - frame["actual_kwh"]
    frame["abs_error_kwh"] = frame["error_kwh"].abs()
    frame["baseline_abs_error_kwh"] = (
        frame["baseline_kwh"] - frame["actual_kwh"]
    ).abs()
    frame["month"] = frame["date"].dt.to_period("M").astype(str)
    return frame


def period_error_summary(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["month", "rf_mae", "baseline_mae", "days"])
    return (
        frame.groupby("month", observed=True)
        .agg(rf_mae=("abs_error_kwh", "mean"), baseline_mae=("baseline_abs_error_kwh", "mean"), days=("date", "size"))
        .reset_index()
    )


def format_number(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")


def format_date(value) -> str:
    return pd.Timestamp(value).strftime("%d/%m/%Y")


def csv_bytes(frame: pd.DataFrame) -> bytes:
    """UTF-8 with BOM for accurate Vietnamese characters when opened in Excel."""
    return frame.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig")
