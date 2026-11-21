"""Verify that the committed UCI and OPSD results are coherent and independent.

These checks use only small published CSV/JSON files, not downloaded source
measurements, and do not assert that HDFS is running on a user's computer.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_uci_provenance_and_chronological_split():
    folder = ROOT / "results" / "uci"
    quality = json.loads((folder / "quality.json").read_text(encoding="utf-8"))
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    test = pd.read_csv(folder / "predictions.csv", parse_dates=["date"])

    assert quality["data_provenance"] == metrics["data_provenance"] == "uci"
    assert quality["raw_rows"] == 2_075_259
    assert quality["clean_unique_rows"] > 2_000_000
    assert quality["raw_rows"] == quality["invalid_rows"] + quality["valid_before_dedup"]
    assert metrics["status"] == "trained"
    assert metrics["train_rows"] + metrics["test_rows"] == metrics["days_used"]
    assert len(test) == metrics["test_rows"]
    assert test["date"].is_monotonic_increasing
    assert test["date"].min().strftime("%Y-%m-%d") == metrics["test_start"]
    assert test["date"].max().strftime("%Y-%m-%d") == metrics["test_end"]
    assert not test[["actual_kwh", "rf_prediction_kwh", "baseline_kwh"]].isna().any().any()
    assert test["actual_kwh"].ge(0).all()
    mae = (test["actual_kwh"] - test["rf_prediction_kwh"]).abs().mean()
    baseline_mae = (test["actual_kwh"] - test["baseline_kwh"]).abs().mean()
    assert mae == pytest.approx(metrics["random_forest"]["mae"], abs=1e-6)
    assert baseline_mae == pytest.approx(metrics["baseline_previous_day"]["mae"], abs=1e-6)


def test_opsd_geographic_provenance_complete_year_and_units():
    folder = ROOT / "results" / "regions"
    meta = json.loads((folder / "quality.json").read_text(encoding="utf-8"))
    daily = pd.read_csv(folder / "daily.csv", parse_dates=["date"])
    monthly = pd.read_csv(folder / "monthly.csv")
    hourly = pd.read_csv(folder / "hourly_profile.csv")
    assert meta["provenance"] == "opsd"
    assert meta["year"] == 2019 and meta["timezone"] == "UTC"
    assert meta["unit"] == {"hourly": "MW", "daily": "GWh", "monthly": "GWh"}
    assert set(meta["countries"]) == {"DE", "FR", "IT", "ES", "GB"}
    assert len(daily) == 5 * 365
    assert set(daily["date"].dt.year) == {2019}
    assert daily["observed_hours"].between(1, 24).all()
    assert daily["coverage"].between(0, 1).all()
    assert daily["observed_gwh"].gt(0).all()
    assert hourly["mean_load_mw"].gt(0).all()
    for code, one_country in daily.groupby("country"):
        month = monthly[monthly["country"] == code]
        assert len(one_country) == 365
        assert len(month) == 12
        assert one_country["observed_hours"].sum() == meta["countries"][code]["observed_hours"]
        assert month["observed_gwh"].sum() == pytest.approx(one_country["observed_gwh"].sum(), rel=1e-10)
        assert month["observed_hours"].sum() == one_country["observed_hours"].sum()


def test_uci_and_opsd_are_never_same_unit_or_population():
    uci = json.loads((ROOT / "results/uci/metrics.json").read_text())
    region = json.loads((ROOT / "results/regions/quality.json").read_text())
    assert uci["target_unit"] == "kWh/day"
    assert region["unit"]["daily"] == "GWh"
    assert region["data_kind"].startswith("national")
    assert uci["data_provenance"] != region["provenance"]
