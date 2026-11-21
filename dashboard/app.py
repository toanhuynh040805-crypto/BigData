"""BigData Energy Intelligence — historical UCI analysis & reproducible AI results.

Designed to run directly from committed CSV/JSON. No Java or PySpark is
needed just to present the project in class.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.analytics import prepare_daily, prepare_predictions, select_daily
from dashboard.pages_explore import render_devices, render_overview, render_trends
from dashboard.pages_insights import render_data, render_forecast, render_quality

REQUIRED = ("daily.csv", "monthly.csv", "hourly_profile.csv", "quality.json", "metrics.json")
PUBLISHED = ROOT / "results" / "uci"
LOCAL = ROOT / "data" / "outputs"
PAGES = [
    "🏠 Tổng quan",
    "📊 Xu hướng & cao điểm",
    "🔌 Nhánh thiết bị",
    "🧠 Dự báo AI",
    "🛡️ Chất lượng dữ liệu",
    "📥 Dữ liệu & báo cáo",
]

st.set_page_config(
    page_title="Energy Intelligence | BigData",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    f"<style>{(ROOT / 'dashboard' / 'style.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Đang tải dữ liệu phân tích...")
def _csv(file_path: str, modified: float) -> pd.DataFrame:
    return pd.read_csv(file_path)


@st.cache_data(show_spinner=False)
def _json(file_path: str, modified: float) -> dict:
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def csv_from(directory: Path, filename: str, optional: bool = False) -> pd.DataFrame:
    path = directory / filename
    if not path.is_file():
        if optional:
            return pd.DataFrame()
        raise FileNotFoundError(path)
    return _csv(str(path), path.stat().st_mtime)


def json_from(directory: Path, filename: str) -> dict:
    path = directory / filename
    return _json(str(path), path.stat().st_mtime)


def source_available(directory: Path) -> bool:
    return all((directory / name).is_file() for name in REQUIRED)


sources = {}
if source_available(PUBLISHED):
    sources["UCI thật · Kết quả GitHub"] = PUBLISHED
if source_available(LOCAL):
    sources["Kết quả Spark · Trên máy"] = LOCAL

if not sources:
    st.error("Chưa tìm thấy bộ dữ liệu đầu ra để hiển thị Dashboard.")
    st.info(
        "Dùng mã nguồn GitHub đầy đủ (thư mục results/uci), "
        "hoặc chạy scripts/download_data.py rồi scripts/run_pipeline.py."
    )
    st.code(
        "cd E:\\BigData\n"
        "git pull origin main\n"
        ".\\.venv\\Scripts\\python.exe -m streamlit run dashboard/app.py",
        language="powershell",
    )
    st.stop()

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚡ ENERGY INTELLIGENCE</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">BIG DATA · CAPSTONE PROJECT</div>', unsafe_allow_html=True)
    st.divider()
    navigation = st.radio("KHÁM PHÁ DỮ LIỆU", PAGES, label_visibility="visible")
    st.divider()
    st.markdown("**Nguồn dữ liệu**")
    selected_source = st.selectbox("Bộ kết quả", list(sources), label_visibility="collapsed")
    if st.button("↻ Nạp lại tệp dữ liệu", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("Nguồn công bố trên GitHub được ưu tiên; kết quả chạy lại trên máy là lựa chọn riêng.")

result_dir = sources[selected_source]
try:
    daily = prepare_daily(csv_from(result_dir, "daily.csv"))
    hourly = csv_from(result_dir, "hourly_profile.csv")
    quality = json_from(result_dir, "quality.json")
    metrics = json_from(result_dir, "metrics.json")
    predictions_raw = csv_from(result_dir, "predictions.csv", optional=True)
    predictions = (
        prepare_predictions(predictions_raw)
        if not predictions_raw.empty
        else pd.DataFrame()
    )
    forecast = csv_from(result_dir, "forecast.csv", optional=True)
    if not forecast.empty:
        forecast["date"] = pd.to_datetime(forecast["date"], errors="coerce")
        forecast["predicted_kwh"] = pd.to_numeric(forecast["predicted_kwh"], errors="coerce")
        forecast = forecast.dropna(subset=["date", "predicted_kwh"])
    hourly["hour"] = pd.to_numeric(hourly["hour"], errors="coerce")
    hourly["mean_power_kw"] = pd.to_numeric(hourly["mean_power_kw"], errors="coerce")
    hourly = hourly.dropna(subset=["hour", "mean_power_kw"]).sort_values("hour")
except (OSError, ValueError, KeyError) as error:
    st.error(f"Lỗi đọc dữ liệu: {error}")
    st.caption("Kiểm tra cấu trúc dữ liệu; có thể tải lại bằng git pull origin main.")
    st.stop()

if daily.empty:
    st.error("Bảng ngày không có dữ liệu hợp lệ.")
    st.stop()

first, last = daily["date"].min().date(), daily["date"].max().date()
with st.sidebar:
    st.divider()
    st.markdown("**Bộ lọc phân tích**")
    period = st.selectbox(
        "Khoảng thời gian",
        ["Toàn bộ dữ liệu", "12 tháng cuối", "90 ngày cuối", "Tùy chọn"],
    )
    if period == "Toàn bộ dữ liệu":
        start, end = first, last
    elif period == "12 tháng cuối":
        start, end = max(first, last - timedelta(days=365)), last
    elif period == "90 ngày cuối":
        start, end = max(first, last - timedelta(days=89)), last
    else:
        chosen = st.date_input(
            "Chọn từ ngày → đến ngày",
            value=(first, last),
            min_value=first, max_value=last,
        )
        if not isinstance(chosen, (tuple, list)) or len(chosen) != 2:
            st.info("Chọn đủ cả ngày bắt đầu và kết thúc.")
            st.stop()
        start, end = chosen
    minimum = st.slider(
        "Bao phủ tối thiểu mỗi ngày",
        0, 100, 0, step=5,
        format="%d%%",
        help="Lọc những ngày có tỷ lệ phút đo hợp lệ dưới ngưỡng. "
             "Không thay đổi tập huấn luyện/test của mô hình đã lưu.",
    ) / 100
    st.caption(f"{start:%d/%m/%Y} → {end:%d/%m/%Y}")
    st.divider()
    st.markdown(
        "[Nguồn UCI](https://doi.org/10.24432/C58K54) · "
        "[Mã nguồn GitHub](https://github.com/toanhuynh040805-crypto/BigData)"
    )
    st.caption("Historical data 2006–2010 · One household · CC BY 4.0")

if start > end:
    st.error("Ngày bắt đầu phải nhỏ hơn ngày kết thúc.")
    st.stop()
selected = select_daily(daily, start, end, minimum)
if selected.empty:
    st.warning("Bộ lọc hiện tại không có ngày phù hợp. Hãy mở rộng khoảng thời gian hoặc giảm bao phủ tối thiểu.")
    st.stop()

is_uci = quality.get("data_provenance") == "uci" and metrics.get("data_provenance") == "uci"
st.markdown(
    '<div class="hero">'
    '<div class="hero-eyebrow">BÁO CÁO ĐỒ ÁN CUỐI KỲ · NHẬP MÔN BIG DATA</div>'
    '<h1>Phân tích & dự báo<br>tiêu thụ điện năng</h1>'
    '<p>Hệ thống phân tích lịch sử sử dụng điện của một hộ gia đình bằng Apache Spark; '
    'khám phá chu kỳ tiêu thụ, đánh giá chất lượng và dự báo với Random Forest Regression.</p>'
    '<div class="hero-pills"><span>⚡ APACHE SPARK</span><span>🧠 RANDOM FOREST</span>'
    '<span>📈 STREAMLIT + PLOTLY</span><span>🗂 UCI 2006–2010</span></div>'
    '</div>',
    unsafe_allow_html=True,
)

if is_uci:
    st.success(
        "Nguồn đang xem: UCI Household Power Consumption (số liệu lịch sử thực). "
        "Kết quả mô hình được lấy từ pipeline Spark; các biểu đồ ngày tùy thuộc bộ lọc."
    )
elif quality.get("data_provenance") == "synthetic" or metrics.get("data_provenance") == "synthetic":
    st.error(
        "DỮ LIỆU GIẢ LẬP (SYNTHETIC): chỉ để kiểm thử giao diện, "
        "không dùng các chỉ số này để nộp báo cáo hoặc minh chứng học thuật."
    )
else:
    st.warning("Nguồn dữ liệu chưa được xác nhận là UCI; kiểm tra chất lượng và xuất xứ trước khi trình bày.")

page = navigation
if page == PAGES[0]:
    render_overview(selected, hourly)
elif page == PAGES[1]:
    render_trends(selected, hourly)
elif page == PAGES[2]:
    render_devices(selected)
elif page == PAGES[3]:
    st.caption("Chú ý: trang dự báo sử dụng cố định toàn bộ tập KIỂM TRA theo thời gian, không chịu bộ lọc ngày.")
    render_forecast(metrics, predictions, forecast)
elif page == PAGES[4]:
    render_quality(selected, daily, quality)
else:
    render_data(selected, quality, metrics, selected_source, predictions)

st.markdown(
    '<div class="footer">© BIG DATA ENERGY INTELLIGENCE · Đề tài 9. '
    'Nguồn: UCI Machine Learning Repository — Hebrail & Berard, DOI 10.24432/C58K54. '
    'Đơn vị năng lượng: kWh; công suất: kW. Kết quả chỉ phản ánh một hộ và giai đoạn dữ liệu lịch sử.</div>',
    unsafe_allow_html=True,
)
