"""Interactive Streamlit dashboard for saved Spark aggregates (no Spark in UI)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "outputs"

st.set_page_config(page_title="BigData | Phân tích điện năng", page_icon="⚡", layout="wide")
st.title("⚡ Phân tích và dự báo tiêu thụ điện năng")
st.caption("Đồ án Nhập môn Big Data · Apache Spark / PySpark · Một hộ gia đình")

required = ["daily.csv", "monthly.csv", "hourly_profile.csv", "quality.json", "metrics.json"]
missing = [name for name in required if not (RESULTS / name).exists()]
if missing:
    st.error("Chưa có dữ liệu để hiển thị: " + ", ".join(missing))
    st.code(
        "python scripts/download_data.py\n"
        "python scripts/run_pipeline.py --data-provenance uci\n"
        "streamlit run dashboard/app.py",
        language="powershell",
    )
    st.stop()


@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


with st.sidebar:
    st.header("Bộ lọc")
    if st.button("Làm mới dữ liệu"):
        st.cache_data.clear()
        st.rerun()

daily = load_csv(str(RESULTS / "daily.csv"))
monthly = load_csv(str(RESULTS / "monthly.csv"))
hourly = load_csv(str(RESULTS / "hourly_profile.csv"))
quality = load_json(str(RESULTS / "quality.json"))
metrics = load_json(str(RESULTS / "metrics.json"))

daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
daily = daily.dropna(subset=["date"]).sort_values("date")
if daily.empty:
    st.warning("Không có ngày quan sát hợp lệ.")
    st.stop()

start_default, end_default = daily["date"].min().date(), daily["date"].max().date()
with st.sidebar:
    start = st.date_input("Từ ngày", value=start_default, min_value=start_default, max_value=end_default)
    end = st.date_input("Đến ngày", value=end_default, min_value=start_default, max_value=end_default)
    st.caption("Đơn vị năng lượng: kWh; công suất: kW.")

if start > end:
    st.error("Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc.")
    st.stop()

selected = daily.loc[(daily["date"].dt.date >= start) & (daily["date"].dt.date <= end)].copy()
if selected.empty:
    st.warning("Không có dữ liệu trong khoảng thời gian này.")
    st.stop()

provenance = quality.get("data_provenance", "other")
if provenance == "synthetic":
    st.warning("ĐANG HIỂN THỊ DỮ LIỆU TỔNG HỢP NHÂN TẠO (SYNTHETIC) – chỉ dùng demo, không dùng làm kết quả nghiên cứu.")
elif provenance != "uci":
    st.info("Nguồn dữ liệu chưa được xác nhận bằng tham số --data-provenance uci; hãy kiểm tra trước khi báo cáo.")

st.info(
    "Bộ dữ liệu mô tả **một hộ gia đình tại Pháp (2006–2010)**, "
    "không phản ánh tiêu thụ điện của hiện tại. Ba sub-metering là **nhánh thiết bị**, không phải khu vực địa lý."
)

a, b, c, d = st.columns(4)
a.metric("Tổng điện đã đo", f"{selected['energy_kwh'].sum():,.1f} kWh")
b.metric("Trung bình/ngày quan sát", f"{selected['energy_kwh'].mean():,.2f} kWh")
c.metric("Ngày có bản ghi", f"{len(selected):,}")
d.metric("Bao phủ trung bình", f"{selected['coverage'].mean():.1%}")

tab1, tab2, tab3 = st.tabs(["📊 Tổng quan", "🏠 Nhánh thiết bị", "🧠 Dự báo"])

with tab1:
    st.subheader("Tiêu thụ điện từng ngày")
    fig = px.line(selected, x="date", y="energy_kwh", labels={"date": "Ngày", "energy_kwh": "Điện năng (kWh)"})
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Điện năng tính bằng tổng công suất trung bình theo phút / 60; ngày có thiếu mẫu không được tự động nội suy.")

    m = monthly[
        (monthly["month"] >= start.strftime("%Y-%m"))
        & (monthly["month"] <= end.strftime("%Y-%m"))
    ]
    st.subheader("Tổng điện năng theo tháng")
    st.plotly_chart(
        px.bar(m, x="month", y="energy_kwh",
               labels={"month": "Tháng", "energy_kwh": "Điện năng (kWh)"}),
        use_container_width=True,
    )
    st.subheader("Công suất trung bình theo giờ trong ngày")
    st.plotly_chart(
        px.line(hourly, x="hour", y="mean_power_kw", markers=True,
                labels={"hour": "Giờ (0–23)", "mean_power_kw": "Công suất (kW)"}),
        use_container_width=True,
    )
    st.caption("Biểu đồ theo giờ là đặc trưng trên toàn bộ dữ liệu, không chịu tác động bộ lọc ngày.")

with tab2:
    st.subheader("Ba nhánh thiết bị điện")
    names = {
        "sub1_kwh": "Bếp",
        "sub2_kwh": "Giặt / thiết bị phụ",
        "sub3_kwh": "Bình nước nóng / điều hòa",
    }
    available = [column for column in names if column in selected]
    long = selected.melt(
        id_vars="date", value_vars=available,
        var_name="Nhánh", value_name="Điện năng (kWh)",
    )
    long["Nhánh"] = long["Nhánh"].map(names)
    st.plotly_chart(
        px.area(long, x="date", y="Điện năng (kWh)", color="Nhánh"),
        use_container_width=True,
    )
    st.caption(
        "Sub_metering là điện năng đo theo phút (Wh), quy đổi sang kWh. "
        "Không nhất thiết cộng lại bằng điện năng toàn hộ vì còn thiết bị không được phân nhánh."
    )

with tab3:
    st.subheader("Đánh giá Random Forest trên tập thời gian kiểm tra")
    if metrics.get("status") != "trained":
        st.warning(metrics.get("message", "Chưa có đủ ngày hợp lệ để huấn luyện mô hình."))
    else:
        rf, baseline = metrics["random_forest"], metrics["baseline_previous_day"]
        st.caption(
            f"Train: {metrics['train_rows']} ngày | Test: {metrics['test_rows']} ngày "
            f"({metrics['test_start']} – {metrics['test_end']}); dự báo một ngày tiếp theo."
        )
        r1, r2, r3 = st.columns(3)
        r1.metric("MAE Random Forest", f"{rf['mae']:.3f} kWh")
        r2.metric("RMSE Random Forest", f"{rf['rmse']:.3f} kWh")
        r3.metric("MAE Baseline", f"{baseline['mae']:.3f} kWh")
        scores = pd.DataFrame(
            [
                {"Phương pháp": "Random Forest", "MAE (kWh)": rf["mae"], "RMSE (kWh)": rf["rmse"]},
                {"Phương pháp": "Lặp lại hôm qua", "MAE (kWh)": baseline["mae"], "RMSE (kWh)": baseline["rmse"]},
            ]
        )
        st.dataframe(scores, use_container_width=True, hide_index=True)
        predictions = load_csv(str(RESULTS / "predictions.csv"))
        if not predictions.empty:
            comparison = predictions.melt(
                id_vars="date",
                value_vars=["actual_kwh", "rf_prediction_kwh", "baseline_kwh"],
                var_name="Loại", value_name="kWh",
            )
            st.plotly_chart(
                px.line(comparison, x="date", y="kWh", color="Loại"),
                use_container_width=True,
            )
        next_day = load_csv(str(RESULTS / "forecast.csv"))
        if not next_day.empty:
            f = next_day.iloc[0]
            st.success(f"Dự báo ngày kế tiếp trong chuỗi ({f['date']}): **{f['predicted_kwh']:.2f} kWh**")
            st.caption("Đây là ngày tiếp theo sau ngày cuối của bộ dữ liệu, KHÔNG phải dự báo nhu cầu điện hôm nay.")
        else:
            st.warning("Không đủ bảy ngày lịch sử liên tiếp có chất lượng cao để dự báo ngày tiếp theo.")

st.divider()
with st.expander("Chất lượng dữ liệu và phương pháp"):
    q1, q2, q3 = st.columns(3)
    q1.metric("Dòng nguồn", f"{quality.get('raw_rows', 0):,}")
    q2.metric("Dòng sạch duy nhất", f"{quality.get('clean_unique_rows', 0):,}")
    q3.metric("Dòng trùng đã loại", f"{quality.get('duplicates_removed', 0):,}")
    st.json(quality)
    st.caption(
        "Mốc thời gian gốc không chứa múi giờ; hệ thống giữ giờ hiển thị để nhóm dữ liệu, "
        "không tự diễn giải chuyển đổi DST. Tỷ lệ bao phủ giúp nhận diện ngày bị thiếu mẫu."
    )

st.caption(
    "Nguồn: Hebrail & Berard, UCI Individual Household Electric Power Consumption "
    "(CC BY 4.0; DOI: 10.24432/C58K54)."
)
