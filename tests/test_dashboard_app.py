"""Streamlit UI smoke test for all pages against committed UCI aggregates."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [
    "🏠 Tổng quan",
    "📊 Xu hướng & cao điểm",
    "🔌 Nhánh thiết bị",
    "🧠 Dự báo AI",
    "🛡️ Chất lượng dữ liệu",
    "📥 Dữ liệu & báo cáo",
]


def test_six_pages_render_from_real_published_results():
    assert (ROOT / "results" / "uci" / "daily.csv").exists()
    app = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=90)
    app.run()
    assert not app.exception, app.exception
    for page in PAGES:
        app.radio[0].set_value(page).run()
        assert not app.exception, f"Page {page}: {app.exception}"
