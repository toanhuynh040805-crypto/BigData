"""Forecast evaluation, quality audit, and reproducible data exports."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import (
    DEVICE_LABELS, csv_bytes, format_date, format_number, monthly_from_daily,
    period_error_summary,
)
from dashboard.ui import BLUE, CORAL, GOLD, PALETTE, TEAL, note, plot, section


def render_forecast(metrics: dict, predictions: pd.DataFrame, forecast: pd.DataFrame) -> None:
    section("04 / Predictive analytics", "Dự báo điện năng với Random Forest",
            "Đánh giá chỉ dùng tập kiểm tra theo thứ tự thời gian; không trộn tập train và test.")
    if metrics.get("status") != "trained":
        st.warning(metrics.get("message", "Mô hình chưa đủ dữ liệu để huấn luyện."))
        return
    rf, base = metrics["random_forest"], metrics["baseline_previous_day"]
    improvement = (base["mae"] - rf["mae"]) / base["mae"] * 100 if base["mae"] else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("MAE · Random Forest", f"{format_number(rf['mae'], 3)} kWh")
    k2.metric("RMSE · Random Forest", f"{format_number(rf['rmse'], 3)} kWh")
    k3.metric("R² · Tập test", f"{format_number(rf['r2'], 3)}")
    k4.metric("Thay đổi MAE so với baseline",
              f"{format_number(improvement, 1)}%" if improvement is not None else "—",
              delta="Giảm sai số" if improvement is not None and improvement >= 0 else "Không cải thiện",
              delta_color="off")
    st.info(
        f"Huấn luyện: **{metrics.get('train_rows', 0):,} ngày** · "
        f"Kiểm tra: **{metrics.get('test_rows', 0):,} ngày** "
        f"({metrics.get('test_start')} → {metrics.get('test_end')}). "
        "Đầu ra là kWh/ngày; baseline là giá trị của ngày trước đó."
    )
    if not forecast.empty and metrics.get("next_day_forecast_available"):
        item = forecast.iloc[0]
        date_text = format_date(item["date"])
        note(f"<strong>Dự báo trong giai đoạn lịch sử:</strong> {date_text} ≈ "
             f"<strong>{format_number(item['predicted_kwh'], 2)} kWh</strong>. "
             "Ngày này nằm trong bộ dữ liệu cũ (2006–2010), "
             "không phải điện năng của năm hiện tại.")
    else:
        st.warning("Chưa có dự báo ngày kế tiếp trong chuỗi lịch sử.")

    if predictions.empty:
        st.info("Chưa có predictions.csv cho tập kiểm tra.")
        return
    section("Kiểm định theo thời gian", "Thực tế và hai phương pháp dự báo")
    last_n = st.selectbox("Số ngày kiểm tra hiển thị", ["Tất cả", 30, 60, 120],
                          index=2, key="forecast_window")
    visible = predictions if last_n == "Tất cả" else predictions.tail(int(last_n))
    fig = go.Figure()
    for column, name, color, dash in [
        ("actual_kwh", "Thực tế", "#19364B", None),
        ("rf_prediction_kwh", "Random Forest", TEAL, None),
        ("baseline_kwh", "Hôm trước (baseline)", GOLD, "dot"),
    ]:
        fig.add_trace(go.Scatter(
            x=visible["date"], y=visible[column], name=name, mode="lines",
            line=dict(color=color, width=2.2, dash=dash),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} kWh<extra></extra>",
        ))
    fig.update_yaxes(title="kWh/ngày")
    plot(fig, 375)

    left, right = st.columns(2)
    with left:
        st.subheader("So sánh độ đo MAE và RMSE")
        measures = pd.DataFrame([
            {"Mô hình": "Random Forest", "MAE": rf["mae"], "RMSE": rf["rmse"]},
            {"Mô hình": "Baseline", "MAE": base["mae"], "RMSE": base["rmse"]},
        ])
        long = measures.melt(id_vars="Mô hình", var_name="Độ đo", value_name="kWh")
        fig = px.bar(long, x="Độ đo", y="kWh", color="Mô hình", barmode="group",
                     color_discrete_map={"Random Forest": TEAL, "Baseline": GOLD},
                     text_auto=".2f")
        plot(fig, 330)
    with right:
        st.subheader("Phân bố sai số Random Forest")
        fig = px.histogram(predictions, x="error_kwh", nbins=36,
                           color_discrete_sequence=[BLUE],
                           labels={"error_kwh": "Dự báo − thực tế (kWh)"})
        fig.add_vline(x=0, line_width=2, line_dash="dash", line_color=CORAL)
        fig.update_layout(showlegend=False)
        plot(fig, 330)

    section("Phân tích sai số", "Sai số trung bình theo tháng trên tập kiểm tra")
    comparison = period_error_summary(predictions)
    if not comparison.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=comparison["month"], y=comparison["rf_mae"],
                                 mode="lines+markers", name="MAE Random Forest",
                                 line=dict(color=TEAL, width=3)))
        fig.add_trace(go.Scatter(x=comparison["month"], y=comparison["baseline_mae"],
                                 mode="lines+markers", name="MAE baseline",
                                 line=dict(color=GOLD, width=2, dash="dot")))
        fig.update_yaxes(title="MAE (kWh/ngày)")
        plot(fig, 320)
    worst = predictions.nlargest(8, "abs_error_kwh")[
        ["date", "actual_kwh", "rf_prediction_kwh", "abs_error_kwh"]
    ].copy()
    worst.columns = ["Ngày", "Thực tế (kWh)", "Dự báo (kWh)", "Sai số tuyệt đối (kWh)"]
    with st.expander("8 ngày mô hình dự báo sai lệch lớn nhất"):
        st.dataframe(worst, use_container_width=True, hide_index=True)

    section("Giải thích mô hình", "Phương pháp và giới hạn")
    st.markdown(
        """
        - **Đầu vào:** lag-1, lag-7, trung bình bảy ngày trước và ba đặc trưng lịch.
        - **Tránh rò rỉ tương lai:** đầu vào chỉ lấy trước ngày cần dự báo.
        - **Phân chia:** 80% ngày có dữ liệu đạt chuẩn đầu tiên để huấn luyện;
          20% ngày cuối để đánh giá khách quan, không chia ngẫu nhiên.
        - **MAE/RMSE:** thấp hơn là tốt hơn; R² có thể âm khi mô hình kém.
        - **Giới hạn:** một hộ, thiếu thời tiết và giá điện, không khẳng định dự báo
          cho năm hiện tại hoặc dự báo nhiều tháng.
        """
    )
    st.download_button("⬇ Tải kết quả dự báo kiểm tra (.csv)",
                       data=csv_bytes(predictions.drop(columns=["month"])),
                       file_name="du_bao_tap_kiem_tra.csv", mime="text/csv")


def render_quality(selected: pd.DataFrame, daily: pd.DataFrame, quality: dict) -> None:
    section("05 / Data governance", "Chất lượng và độ tin cậy dữ liệu",
            "Bảng kiểm chứng từ log tiền xử lý Spark và thống kê bao phủ từng ngày.")
    raw = int(quality.get("raw_rows", 0))
    clean = int(quality.get("clean_unique_rows", 0))
    bad = int(quality.get("invalid_rows", 0))
    duplicate = int(quality.get("duplicates_removed", 0))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Bản ghi nguồn", f"{raw:,}")
    k2.metric("Bản ghi sạch", f"{clean:,}")
    k3.metric("Dòng không hợp lệ", f"{bad:,}",
              f"{bad / raw:.2%} nguồn" if raw else "—", delta_color="off")
    k4.metric("Dòng trùng đã loại", f"{duplicate:,}")
    st.caption("Các chỉ số bản ghi ở trên là của toàn bộ nguồn UCI, không chịu bộ lọc ngày.")

    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("Độ bao phủ phép đo từng ngày")
        fig = go.Figure(go.Scatter(
            x=selected["date"], y=selected["coverage"] * 100,
            mode="lines", name="Tỷ lệ bao phủ",
            line=dict(width=2, color=TEAL),
            hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=90, line_color=CORAL, line_dash="dash",
                      annotation_text="Ngưỡng huấn luyện 90%")
        fig.update_yaxes(title="Bao phủ (%)", range=[0, 103])
        plot(fig, 335)
    with right:
        st.subheader("Phân bố độ bao phủ toàn kỳ")
        buckets = pd.cut(
            daily["coverage"], [-0.0001, 0.5, 0.9, 1.0, 1.0001],
            labels=["< 50%", "50–<90%", "90–<100%", "100%"], right=False,
        )
        count = buckets.value_counts(sort=False).rename_axis("Tỷ lệ").reset_index(name="Số ngày")
        count["Tỷ lệ"] = count["Tỷ lệ"].astype(str)
        fig = px.bar(count, x="Tỷ lệ", y="Số ngày", text="Số ngày",
                     color="Tỷ lệ", color_discrete_sequence=PALETTE)
        fig.update_layout(showlegend=False)
        plot(fig, 335)
    st.caption("Bao phủ = số phút hợp lệ khác nhau / 1.440; không suy ra năng lượng trong các phút bị thiếu.")
    incomplete = daily.loc[daily["coverage"] < 0.9].sort_values("coverage")
    h1, h2, h3 = st.columns(3)
    h1.metric("Ngày có dữ liệu toàn kỳ", f"{len(daily):,}")
    h2.metric("Ngày dưới 90% bao phủ", f"{len(incomplete):,}")
    h3.metric("Bao phủ TB trong bộ lọc", f"{selected['coverage'].mean():.2%}")
    with st.expander("Xem những ngày thiếu dữ liệu nhiều nhất"):
        if incomplete.empty:
            st.success("Tất cả các ngày có dữ liệu đều đạt ≥90% bao phủ.")
        else:
            table = incomplete.head(30)[["date", "valid_minutes", "coverage", "energy_kwh"]].copy()
            table.columns = ["Ngày", "Phút hợp lệ", "Tỷ lệ bao phủ", "Điện năng quan sát (kWh)"]
            st.dataframe(table, hide_index=True, use_container_width=True)
            st.download_button("⬇ Tải tất cả ngày dưới 90% (.csv)",
                               data=csv_bytes(incomplete), file_name="ngay_thieu_du_lieu.csv",
                               mime="text/csv")

    section("Phương pháp", "Quy trình làm sạch và quản trị dữ liệu")
    st.markdown(
        """
        1. **Chuẩn hóa thời gian:** nhận định dạng ngày linh hoạt, giữ nguyên
           giờ hiển thị của nguồn và không tự suy diễn giờ mùa hè (DST).
        2. **Loại lỗi:** ngày/giờ sai; công suất thiếu, NaN hoặc âm.
        3. **Trùng thời điểm:** ưu tiên bản ghi đầy đủ hơn, giữ một mẫu theo thời điểm nguồn.
        4. **Quy đổi:** tổng điện năng toàn hộ là tổng kW mỗi phút / 60;
           Sub-metering Wh / 1000.
        5. **Huấn luyện:** chỉ chọn ngày có độ bao phủ ≥90% làm mục tiêu;
           lag phải khớp khoảng cách ngày trên lịch.
        """
    )
    note("Dữ liệu gốc không có UTC offset và có khoảng trống đo đạc. "
         "Không thể kết luận lượng điện thực dùng vào lúc không có mẫu đo.")


def render_data(selected: pd.DataFrame, quality: dict, metrics: dict,
                source_label: str, predictions: pd.DataFrame) -> None:
    section("06 / Reproducibility & export", "Dữ liệu, minh chứng và xuất báo cáo",
            "Tải bảng thống kê và bằng chứng số liệu từ đúng nguồn để đưa vào Word hoặc PowerPoint.")
    col1, col2, col3 = st.columns(3)
    col1.metric("Nguồn hiển thị", source_label)
    col2.metric("Số ngày được lọc", f"{len(selected):,}")
    col3.metric("Định dạng hỗ trợ", "CSV / JSON")
    tab1, tab2, tab3 = st.tabs(["📋 Bảng dữ liệu", "📦 Xuất kết quả", "🔬 Kiến trúc & tài liệu"])
    with tab1:
        st.caption("Một bản ghi tương ứng một ngày; các cột điện năng ở đơn vị kWh.")
        fields = selected[["date", "energy_kwh", "coverage", "valid_minutes", *DEVICE_LABELS]].copy()
        fields = fields.rename(columns={
            "date": "Ngày", "energy_kwh": "Toàn hộ (kWh)",
            "coverage": "Bao phủ", "valid_minutes": "Phút hợp lệ", **DEVICE_LABELS,
        })
        st.dataframe(fields, use_container_width=True, hide_index=True, height=430)
        st.caption(f"{len(fields):,} bản ghi ngày đang hiển thị.")
    with tab2:
        left, right = st.columns(2)
        with left:
            st.subheader("Dữ liệu phân tích")
            st.download_button("⬇ Dữ liệu ngày đã lọc (.csv)", data=csv_bytes(selected),
                               file_name="bigdata_ngay_da_loc.csv", mime="text/csv",
                               use_container_width=True)
            st.download_button("⬇ Tổng hợp tháng đã lọc (.csv)",
                               data=csv_bytes(monthly_from_daily(selected)),
                               file_name="bigdata_thang_da_loc.csv", mime="text/csv",
                               use_container_width=True)
            if not predictions.empty:
                st.download_button("⬇ Kết quả dự báo test (.csv)",
                                   data=csv_bytes(predictions), file_name="bigdata_du_bao.csv",
                                   mime="text/csv", use_container_width=True)
        with right:
            st.subheader("Minh chứng mô hình và chất lượng")
            st.download_button("⬇ Chất lượng dữ liệu (.json)",
                               data=json.dumps(quality, ensure_ascii=False, indent=2).encode("utf-8"),
                               file_name="quality.json", mime="application/json",
                               use_container_width=True)
            st.download_button("⬇ Kết quả đánh giá AI (.json)",
                               data=json.dumps(metrics, ensure_ascii=False, indent=2).encode("utf-8"),
                               file_name="metrics.json", mime="application/json",
                               use_container_width=True)
        st.caption("CSV mã hóa UTF-8 BOM để mở thuận tiện trong Microsoft Excel.")
    with tab3:
        st.subheader("Luồng xử lý và mô hình")
        st.code(
            "UCI household_power_consumption.txt\n"
            "  | 2.075.259 mẫu theo phút\n"
            "  v\n"
            "Apache Spark DataFrame (parse → clean → deduplicate)\n"
            "  |-- Parquet phân vùng năm/tháng\n"
            "  |-- Daily/Monthly/Hourly aggregates → Streamlit\n"
            "  +-- Spark MLlib Random Forest → đánh giá MAE/RMSE/R²\n"
            "                                 → dự báo một ngày tiếp theo",
            language="text",
        )
        st.markdown(
            "**Tài liệu trong repository**\n\n"
            "- [Mã nguồn dự án BigData](https://github.com/toanhuynh040805-crypto/BigData)\n"
            "- [Báo cáo Word](https://github.com/toanhuynh040805-crypto/BigData/blob/main/reports/Bao_cao_BigData_Dien_nang.docx)\n"
            "- [Slide PowerPoint](https://github.com/toanhuynh040805-crypto/BigData/blob/main/reports/Slide_BigData_Dien_nang.pptx)\n"
            "- [Bảng kết quả UCI thật](https://github.com/toanhuynh040805-crypto/BigData/tree/main/results/uci)\n"
            "- [Nguồn gốc bộ dữ liệu UCI, DOI 10.24432/C58K54](https://doi.org/10.24432/C58K54)\n"
        )
        note("Word và PowerPoint tự sinh chỉ là <strong>bản nháp</strong>: "
             "cần điền đúng thông tin giảng viên, hai sinh viên, phân công và rà soát bài trước khi nộp.")
