"""Separate OPSD 2019 national grid load dashboard; not UCI household consumption."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import csv_bytes, format_number
from dashboard.ui import BLUE, GOLD, PALETTE, TEAL, note, plot, section


def load_region_data(base, csv_reader, json_reader):
    """Fail fast if the published OPSD evidence is malformed or mislabeled."""
    needed = ["quality.json", "daily.csv", "monthly.csv", "hourly_profile.csv"]
    missing = [name for name in needed if not (base / name).is_file()]
    if missing:
        raise ValueError("Thiếu kết quả OPSD: " + ", ".join(missing))
    meta = json_reader(base, "quality.json")
    if meta.get("provenance") != "opsd" or meta.get("year") != 2019:
        raise ValueError("Bộ khu vực không đúng nguồn OPSD năm 2019")
    daily = csv_reader(base, "daily.csv")
    months = csv_reader(base, "monthly.csv")
    hours = csv_reader(base, "hourly_profile.csv")
    columns = {
        "daily": {"country", "country_name", "date", "observed_gwh", "observed_hours", "coverage"},
        "monthly": {"country", "country_name", "month", "observed_gwh", "observed_days"},
        "hourly": {"country", "country_name", "hour_utc", "mean_load_mw"},
    }
    for label, frame in (("daily", daily), ("monthly", months), ("hourly", hours)):
        missing_cols = columns[label] - set(frame.columns)
        if missing_cols:
            raise ValueError(f"Dữ liệu OPSD {label} thiếu: {sorted(missing_cols)}")
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily["observed_gwh"] = pd.to_numeric(daily["observed_gwh"], errors="coerce")
    daily["coverage"] = pd.to_numeric(daily["coverage"], errors="coerce")
    months["observed_gwh"] = pd.to_numeric(months["observed_gwh"], errors="coerce")
    hours["mean_load_mw"] = pd.to_numeric(hours["mean_load_mw"], errors="coerce")
    for label, frame in (("daily", daily), ("monthly", months), ("hourly", hours)):
        if frame.empty:
            raise ValueError(f"Bảng {label} OPSD không có dữ liệu")
    if daily["country"].nunique() != 5:
        raise ValueError("Bộ OPSD công bố không có đủ 5 quốc gia")
    return meta, daily, months, hours


def render_regions(meta: dict, daily: pd.DataFrame,
                   months: pd.DataFrame, hours: pd.DataFrame) -> None:
    section(
        "07 / Geographical intelligence",
        "Phân tích phụ tải điện theo quốc gia",
        "Nguồn Open Power System Data (OPSD) · năm 2019 · 5 quốc gia châu Âu.",
    )
    note(
        "<strong>Lưu ý về phạm vi khoa học:</strong> OPSD là phụ tải điện "
        "<strong>toàn quốc</strong>, đơn vị MW và GWh, hoàn toàn độc lập với "
        "dữ liệu <strong>một hộ gia đình UCI (kWh)</strong>. "
        "Không trộn dữ liệu, không dùng OPSD để dự báo hộ gia đình."
    )
    countries = sorted(daily["country"].unique().tolist())
    labels = (daily.drop_duplicates("country").set_index("country")["country_name"].to_dict())
    label_names = [labels[code] for code in countries]
    chosen_labels = st.multiselect(
        "Quốc gia hiển thị",
        options=label_names,
        default=label_names,
        help="Chọn quốc gia để so sánh. Đơn vị đo toàn quốc không chuẩn hóa theo dân số.",
    )
    selected_codes = [code for code in countries if labels[code] in chosen_labels]
    if not selected_codes:
        st.warning("Hãy chọn ít nhất một quốc gia.")
        return
    filtered_daily = daily.loc[daily["country"].isin(selected_codes)].copy()
    filtered_monthly = months.loc[months["country"].isin(selected_codes)].copy()
    filtered_hours = hours.loc[hours["country"].isin(selected_codes)].copy()
    total = (
        filtered_daily.groupby(["country", "country_name"], as_index=False)
        .agg(
            observed_gwh=("observed_gwh", "sum"),
            observed_hours=("observed_hours", "sum"),
            mean_daily_coverage=("coverage", "mean"),
            days=("date", "size"),
        )
        .sort_values("observed_gwh", ascending=False)
    )
    widest = total.iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Số quốc gia đang chọn", str(len(selected_codes)))
    b.metric("Tổng giờ quan sát", f"{int(total['observed_hours'].sum()):,}")
    c.metric("Độ bao phủ bình quân", f"{total['mean_daily_coverage'].mean():.2%}")
    d.metric("Phụ tải lớn nhất", str(widest["country_name"]))
    st.caption("Số liệu năm 2019. Tổng quốc gia khác nhau phản ánh quy mô hệ thống, không chứng minh sử dụng kém hiệu quả.")

    left, right = st.columns([1, 1.15])
    with left:
        st.subheader("Tổng điện năng ghi nhận trong năm")
        fig = px.bar(
            total, y="country_name", x="observed_gwh", orientation="h",
            color="country_name", color_discrete_sequence=PALETTE,
            labels={"country_name": "Quốc gia", "observed_gwh": "Điện năng ghi nhận (GWh)"},
            text_auto=".0f",
        )
        fig.update_layout(showlegend=False)
        plot(fig, 380)
    with right:
        st.subheader("Tương quan tháng giữa các quốc gia")
        fig = px.line(
            filtered_monthly.sort_values("month"),
            x="month", y="observed_gwh",
            color="country_name", markers=True,
            color_discrete_sequence=PALETTE,
            labels={
                "month": "Tháng 2019",
                "observed_gwh": "GWh quan sát/tháng",
                "country_name": "Quốc gia",
            },
        )
        fig.update_xaxes(type="category", tickangle=-30)
        plot(fig, 380)

    section("Đường phụ tải", "Diễn biến điện năng theo ngày",
            "Mỗi điểm là tổng năng lượng của các giờ UTC đã quan sát. Ngày thiếu giờ có thể bị thấp hơn.")
    recent = filtered_daily.sort_values("date")
    fig = px.line(recent, x="date", y="observed_gwh", color="country_name",
                  color_discrete_sequence=PALETTE,
                  labels={
                      "date": "Ngày 2019",
                      "observed_gwh": "GWh/ngày (quan sát)",
                      "country_name": "Quốc gia",
                  })
    plot(fig, 360)

    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Công suất trung bình theo giờ UTC")
        fig = px.line(
            filtered_hours.sort_values("hour_utc"),
            x="hour_utc", y="mean_load_mw",
            color="country_name", markers=True,
            color_discrete_sequence=PALETTE,
            labels={
                "hour_utc": "Giờ UTC (0–23)", "mean_load_mw": "MW trung bình",
                "country_name": "Quốc gia",
            },
        )
        fig.update_xaxes(dtick=2)
        plot(fig, 350)
    with right:
        st.subheader("Tính đầy đủ của dữ liệu")
        coverage = total[["country_name", "observed_hours", "mean_daily_coverage"]].copy()
        coverage.columns = ["Quốc gia", "Giờ có đo", "Bao phủ bình quân"]
        st.dataframe(coverage, use_container_width=True, hide_index=True, height=320)
        st.caption(
            "Bộ năm 2019 có 8.760 giờ UTC. Thiếu giờ không được tự động điền bằng 0 "
            "hay nội suy. So sánh không điều chỉnh theo dân số."
        )

    section("Tính tái lập", "Nguồn dữ liệu và bảng kết quả")
    st.markdown(
        "OPSD Time Series 2020-10-06, dữ liệu từ ENTSO-E Transparency. "
        "[Nguồn chính thức](https://doi.org/10.25832/time_series/2020-10-06). "
        "Các bảng được Spark tổng hợp trực tiếp từ tệp CSV theo giờ của OPSD."
    )
    st.download_button(
        "Tải điện năng ngày theo quốc gia (.csv)",
        data=csv_bytes(filtered_daily),
        file_name="opsd_2019_phu_tai_quoc_gia.csv",
        mime="text/csv",
    )
