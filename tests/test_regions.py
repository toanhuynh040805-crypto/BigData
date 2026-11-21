"""Unit tests for OPSD UTC national-grid energy conversion and missingness."""
from __future__ import annotations
import pytest

def test_mw_to_gwh_with_missing_hour(spark):
    from energy_bigdata.regions import COUNTRIES, hourly_load, regional_aggregates
    cols = ["utc_timestamp", *[x[1] for x in COUNTRIES.values()]]
    rows = [
        ("2019-02-01T00:00:00Z", "1000", "2000", "3000", "4000", "5000"),
        ("2019-02-01T01:00:00Z", "1200", "2200", "3200", "4200", "5200"),
        ("2019-02-01T02:00:00Z", "?", "2200", "3200", "4200", "5200"),
        ("2019-02-01T01:00:00Z", "1200", "2200", "3200", "4200", "5200"),
        ("2020-02-01T00:00:00Z", "9999", "9999", "9999", "9999", "9999"),
    ]
    hourly = hourly_load(spark.createDataFrame(rows, cols), 2019)
    assert hourly.where("country = 'DE'").count() == 2
    assert hourly.where("country = 'FR'").count() == 3
    daily, monthly, profile = regional_aggregates(hourly)
    de = daily.where("country='DE'").first()
    assert de["observed_gwh"] == pytest.approx(2.2)
    assert de["observed_hours"] == 2
    assert de["coverage"] == pytest.approx(2 / 24)
    assert monthly.where("country='DE'").first()["observed_gwh"] == pytest.approx(2.2)
    assert profile.where("country='DE'").count() == 2

def test_missing_country_schema(spark):
    from energy_bigdata.regions import hourly_load
    data = spark.createDataFrame([("2019-01-01T00:00:00Z",)], ["utc_timestamp"])
    with pytest.raises(ValueError, match="missing columns"):
        hourly_load(data)
