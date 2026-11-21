"""Non-Spark tests can run even where Java/PySpark is not available."""
from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path


def _load_script(name: str):
    location = Path(__file__).resolve().parents[1] / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), location)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_sample_generator(tmp_path):
    generator = _load_script("generate_sample.py")
    path = tmp_path / "fixture.txt"
    assert generator.generate(path, days=1) == 1440
    with path.open(encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == 1441
    assert lines[0].startswith("Date;Time;Global_active_power")
    assert lines[1].startswith("01/01/2008;00:00:00;")


def test_extract_only_expected_file(tmp_path):
    downloader = _load_script("download_data.py")
    archive = tmp_path / "archive.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("data/household_power_consumption.txt", "Date;Time\n")
        z.writestr("other.txt", "unrelated")
    out = downloader.extract_dataset(archive, tmp_path / "output.txt")
    assert out.read_text(encoding="utf-8") == "Date;Time\n"


def test_extract_refuses_archive_without_dataset(tmp_path):
    downloader = _load_script("download_data.py")
    archive = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("something_else.txt", "hello")
    try:
        downloader.extract_dataset(archive, tmp_path / "unexpected.txt")
    except ValueError as error:
        assert "exactly one" in str(error)
    else:
        raise AssertionError("Expected archive validation error")
