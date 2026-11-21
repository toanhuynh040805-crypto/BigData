"""Data integrity regressions: flexible dates, duplicates and daily units."""
from __future__ import annotations

import pytest


FIELDS = [
    "Date", "Time", "Global_active_power", "Global_reactive_power", "Voltage",
    "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
]


def test_cleaning_and_energy_units(spark):
    from energy_bigdata.pipeline import aggregates, clean_records, describe_quality, parse_records

    rows = [
        ("1/1/2008", "00:00:00", "1.2", "0.1", "230", "5", "1", "2", "3"),
        ("01/01/2008", "00:00:00", "1.4", "0.1", "230", "5", "1", "2", "3"),
        ("01/01/2008", "00:01:00", "1.8", "0.1", "230", "6", "1", "2", "3"),
        ("01/01/2008", "00:02:00", "?", "?", "?", "?", "?", "?", "?"),
        ("31/02/2008", "00:01:00", "2.0", "0.1", "230", "6", "1", "2", "3"),
    ]
    parsed = parse_records(spark.createDataFrame(rows, FIELDS))
    clean = clean_records(parsed)
    assert clean.count() == 2
    quality = describe_quality(parsed, clean)
    assert quality["raw_rows"] == 5
    assert quality["valid_before_dedup"] == 3
    assert quality["duplicates_removed"] == 1
    assert quality["invalid_rows"] == 2
    daily, monthly, hourly = aggregates(clean)
    row = daily.first()
    assert row["energy_kwh"] == pytest.approx((1.2 + 1.8) / 60)
    assert row["sub1_kwh"] == pytest.approx(0.002)
    assert row["coverage"] == pytest.approx(2 / 1440)
    assert monthly.count() == 1
    assert hourly.count() == 1


def test_no_negative_power(spark):
    from energy_bigdata.pipeline import clean_records, parse_records

    rows = [
        ("2/1/2008", "00:00:00", "-1", "0", "230", "0", "0", "0", "0"),
        ("2/1/2008", "00:01:00", "0", "0", "230", "0", "0", "0", "0"),
    ]
    assert clean_records(parse_records(spark.createDataFrame(rows, FIELDS))).count() == 1
