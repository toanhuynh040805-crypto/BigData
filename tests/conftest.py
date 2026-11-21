"""Shared Spark local fixture. CI runs against Python 3.11 + JDK 17."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(scope="session")
def spark():
    pytest.importorskip("pyspark")
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    from energy_bigdata.pipeline import make_spark

    session = make_spark("local[2]")
    session.sparkContext.setLogLevel("ERROR")
    yield session
    session.stop()
