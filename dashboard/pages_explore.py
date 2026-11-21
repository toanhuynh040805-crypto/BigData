"""Overview, temporal patterns, and device analysis pages."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.analytics import (
    DEVICE_LABELS, anomalies_iqr, calendar_rolling, csv_bytes, device_totals,
    distribution_by_weekday, format_date, format_number, monthly_from_daily,
)
from dashboard.ui import BLUE, CORAL, GOLD, INK, PALETTE, TEAL, note, plot, section


def _line_energy(daily: pd.DataFrame, rolling: int = 7) -> go.Figure:
    smoothed = calendar_rolling(daily, rolling)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily["date"], y=daily["energy_kwh"], mode="lines",
        name="Điện năng theo ngày", line=dict(color=BLUE, width=1.5),
        fill="tozeroy", fillcolor="rgba(73,117,183,0.06)",
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=smoothed["date"], y=smoothed["rolling_kwh"], mode="lines",
        name=f"Trung bình {rolling} ngày liên tục",
        line=dict(color=TEAL, width=3),
        hovertemplate="%{x|%d/%m/%Y}<br>%{y:.2f} kWh<extra></extra>",
    ))
    fig.update_yaxes(title="Điện năng (kWh)")
    return fig


def _monthly_bar(daily: pd.DataFrame) -> go.Figure:
    monthly = monthly_from_daily(daily)
    fig = go.Figure()
    fig.add_bar(
        x=monthly["month"], y=monthly["energy_kwh"], marker_color=TEAL,
        name="Điện năng tháng", hovertemplate="%{x}<br>%{y:,.1f} kWh<extra></extra>",
    )
    fig.update_xaxes(type="category", nticks=12)
    fig.update_yaxes(title="Điện năng đã đo (kWh)")
    return fig


def render_overview(selected: pd.DataFrame, hourly: pd.DataFrame) -> None:
    section("01 / Executive overview", "Tổng quan tiêu thụ điện năng",
            "Các chỉ số và biểu đồ được tính từ đúng khoảng ngày cùng mức bao phủ đang chọn.")
    total = float(selected["energy_kwh"].sum())
    avg = float(selected["energy_kwh"].mean())
    coverage = float(selected["coverage"].mean())
    complete = int((selected["coverage"] >= 0.9).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Điện năng quan sát", f"{format_number(total, 1)} kWh",
              help="Tổng điện năng của các mẫu ghi nhận; không bù điện năng thiếu.")
    c2.metric("Trung bình/ngày có đo", f"{format_number(avg, 2)} kWh")
    c3.metric("Ngày có bản ghi", f"{len(selected):,}")
    c4.metric("Ngày bao phủ ≥90%", f"{complete:,}", f"{coverage:.1%} bao phủ TB",
              delta_color="off")
    st.caption("Ngày thiếu mẫu làm thấp tổng điện năng quan sát; không nội suy điện năng chưa đo.")

    rolling = st.select_slider("Đường xu hướng", options=[7, 14, 30], value=7,
                               format_func=lambda days: f"Trung bình {days} ngày")
    plot(_line_energy(selected, rolling), 360)
    left, right = st.columns([1.25, 1])
    with left:
        section("Phân bổ thời gian", "Điện năng theo tháng",
                "Tháng đầu/cuối trong bộ lọc có thể chỉ chứa một phần ngày.")
        plot(_monthly_bar(selected), 315)
    with right:
        section("Thời điểm sử dụng", "Giờ có công suất cao",
                "Trung bình theo giờ trên TOÀN BỘ nguồn, không chịu bộ lọc ngày.")
        if not hourly.empty:
            fig = px.bar(
                hourly, x="hour", y="mean_power_kw",
                color="mean_power_kw", color_continuous_scale=["#BFE3E3", TEAL],
                labels={"hour": "Giờ trong ngày", "mean_power_kw": "kW trung bình"},
            )
            fig.update_layout(coloraxis_showscale=False, showlegend=False)
            fig.update_xaxes(dtick=2)
            plot(fig, 315)

    section("Insight / Giá trị rút ra", "Nhận xét tự động từ số liệu")
    comparable = selected.loc[selected["coverage"] >= 0.9]
    if comparable.empty:
        note("Không đủ ngày đạt bao phủ ≥90% để so sánh đỉnh tiêu thụ. "
             "Hãy giảm bộ lọc hoặc kiểm tra chất lượng dữ liệu.")
    else:
        peak = comparable.loc[comparable["energy_kwh"].idxmax()]
        monthly = monthly_from_daily(selected)
        peak_month = monthly.loc[monthly["energy_kwh"].idxmax()]
        a, b, c = st.columns(3)
        with a:
            st.markdown('<div class="explain-card"><h4>Ngày tiêu thụ cao nhất</h4>'
                        f'<p><strong>{format_date(peak["date"])}</strong>: '
                        f'{format_number(peak["energy_kwh"], 2)} kWh, '
                        'chỉ xét ngày có độ bao phủ ≥90%.</p></div>', unsafe_allow_html=True)
        with b:
            st.markdown('<div class="explain-card"><h4>Tháng nhiều điện nhất trong bộ lọc</h4>'
                        f'<p><strong>{peak_month["month"]}</strong>: '
                        f'{format_number(peak_month["energy_kwh"], 1)} kWh đo được.'
                        ' Kết quả phụ thuộc số ngày được chọn.</p></div>', unsafe_allow_html=True)
        with c:
            hour_peak = hourly.loc[hourly["mean_power_kw"].idxmax()] if not hourly.empty else None
            if hour_peak is not None:
                st.markdown('<div class="explain-card"><h4>Giờ cao điểm trung bình toàn kỳ</h4>'
                            f'<p><strong>{int(hour_peak["hour"]):02d}:00</strong> — '
                            f'{format_number(hour_peak["mean_power_kw"], 2)} kW.'
                            ' Mức trung bình theo toàn bộ bản ghi.</p></div>', unsafe_allow_html=True)


def render_trends(selected: pd.DataFrame, hourly: pd.DataFrame) -> None:
    section("02 / Time intelligence", "Xu hướng và chu kỳ sử dụng",
            "Phân tích theo ngày trong tuần, tháng/năm và phát hiện giá trị ngoại lệ có giải thích.")
    weekday = distribution_by_weekday(selected)
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Trung bình theo thứ trong tuần")
        fig = px.bar(
            weekday, x="day", y="mean_kwh",
            color="mean_kwh", color_continuous_scale=["#BDD6E8", TEAL],
            labels={"day": "Ngày", "mean_kwh": "kWh/ngày"},
            custom_data=["days"],
        )
        fig.update_traces(hovertemplate="%{x}<br>%{y:.2f} kWh/ngày<br>%{customdata[0]} ngày<extra></extra>")
        fig.update_layout(showlegend=False, coloraxis_showscale=False)
        plot(fig, 345)
    with right:
        st.subheader("Ngày thường và cuối tuần")
        sample = selected.assign(
            group=np.where(selected["weekday"] >= 5, "Cuối tuần", "Ngày thường")
        )
        summary = sample.groupby("group", observed=True).agg(
            average=("energy_kwh", "mean"), days=("date", "size")
        ).reset_index()
        fig = px.bar(summary, x="group", y="average", color="group",
                     color_discrete_map={"Ngày thường": BLUE, "Cuối tuần": GOLD},
                     custom_data=["days"],
                     labels={"group": "Nhóm", "average": "kWh/ngày"})
        fig.update_traces(hovertemplate="%{x}<br>%{y:.2f} kWh/ngày<br>%{customdata[0]} ngày<extra></extra>")
        fig.update_layout(showlegend=False)
        plot(fig, 345)
    st.caption("Trung bình theo những ngày còn lại sau bộ lọc, không chuẩn hóa năng lượng bị thiếu.")

    section("Mùa vụ", "Bản đồ nhiệt điện năng theo tháng và năm")
    months = monthly_from_daily(selected)
    months["year"] = months["month"].str[:4].astype(int)
    months["month_no"] = months["month"].str[5:7].astype(int)
    heat = months.pivot(index="year", columns="month_no", values="energy_kwh").reindex(columns=range(1, 13))
    if not heat.empty:
        fig = go.Figure(go.Heatmap(
            z=heat.to_numpy(dtype=float), x=[f"T{i}" for i in range(1, 13)],
            y=[str(y) for y in heat.index], colorscale=[[0, "#EFF7F7"], [1, TEAL]],
            colorbar=dict(title="kWh"), hoverongaps=False,
            hovertemplate="%{y} · %{x}<br>%{z:.1f} kWh<extra></extra>",
        ))
        fig.update_layout(showlegend=False)
        plot(fig, 310)
    st.caption("Tháng một phần trong bộ lọc hoặc thiếu dữ liệu có tổng thấp hơn; không so sánh như tháng đủ ngày.")

    section("Phát hiện thống kê", "Ngày tiêu thụ khác biệt")
    flagged, settings = anomalies_iqr(selected)
    if settings["status"] != "ok":
        st.info("Cần ít nhất 20 ngày đạt độ bao phủ ≥90% để phân tích ngoại lệ theo IQR.")
    else:
        p1, p2, p3 = st.columns(3)
        p1.metric("Ngày được so sánh", f"{settings['sample']:,}")
        p2.metric("Ngưỡng cao IQR", f"{format_number(settings['upper'], 2)} kWh")
        p3.metric("Ngày ngoài khoảng IQR", f"{len(flagged)}")
        note("IQR = Q3 − Q1; đánh dấu ngày nằm ngoài [max(0, Q1−1,5×IQR), Q3+1,5×IQR]. "
             "Đây là tín hiệu cần khảo sát, <strong>không phải kết luận thiết bị lỗi hay gian lận điện</strong>.")
        if not flagged.empty:
            view = flagged[["date", "energy_kwh", "coverage", "type"]].copy()
            view.columns = ["Ngày", "Điện năng (kWh)", "Bao phủ", "Loại"]
            st.dataframe(view, hide_index=True, use_container_width=True)
            st.download_button("Tải ngày bất thường (.csv)",
                               data=csv_bytes(view), file_name="ngay_bat_thuong.csv", mime="text/csv")
        else:
            st.success("Không phát hiện giá trị ngoại lệ theo ngưỡng IQR trong khoảng đã chọn.")

    section("Biểu đồ toàn kỳ", "Công suất trung bình theo 24 giờ")
    if not hourly.empty:
        fig = go.Figure(go.Scatter(
            x=hourly["hour"], y=hourly["mean_power_kw"],
            mode="lines+markers", name="kW trung bình",
            line=dict(color=TEAL, width=3), marker=dict(size=7, color=GOLD),
            hovertemplate="%{x}:00<br>%{y:.3f} kW<extra></extra>",
        ))
        fig.update_xaxes(dtick=1, title="Giờ trong ngày (giờ nguồn)")
        fig.update_yaxes(title="Công suất trung bình (kW)")
        plot(fig, 320)
        st.caption("Dữ liệu hourly_profile.csv tổng hợp TOÀN KỲ UCI; không thay đổi khi lọc ngày.")


def render_devices(selected: pd.DataFrame) -> None:
    section("03 / Device intelligence", "Phân tích các nhánh tiêu thụ",
            "Ba sub-metering là ba nhóm thiết bị trong MỘT hộ gia đình, không phải khu vực địa lý.")
    totals = device_totals(selected)
    full_total = float(selected["energy_kwh"].sum())
    known = float(sum(selected[k].fillna(0).sum() for k in DEVICE_LABELS))
    a, b, c, d = st.columns(4)
    for col, (key, label) in zip((a, b, c), DEVICE_LABELS.items()):
        val = float(selected[key].fillna(0).sum())
        col.metric(label, f"{format_number(val, 1)} kWh")
    d.metric("Đã đo theo nhánh", f"{known / full_total:.1%}" if full_total > 0 else "—")
    if known > full_total + 1e-6:
        st.warning("Tổng ba nhánh vượt điện năng toàn hộ trong bộ lọc; không ép phần chênh lệch thành âm.")
    left, right = st.columns([1, 1.4])
    with left:
        st.subheader("Tỷ trọng điện năng quan sát")
        fig = px.pie(totals, names="device", values="energy_kwh", hole=0.61,
                     color="device", color_discrete_sequence=PALETTE)
        fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:.1f} kWh (%{percent})<extra></extra>")
        fig.update_layout(legend=dict(orientation="v", y=0.75, x=0.85))
        plot(fig, 370)
    with right:
        st.subheader("Diễn biến từng nhánh theo ngày")
        long = selected.melt(id_vars="date", value_vars=list(DEVICE_LABELS),
                             var_name="branch", value_name="energy_kwh")
        long["branch"] = long["branch"].map(DEVICE_LABELS)
        fig = px.area(long, x="date", y="energy_kwh", color="branch",
                      color_discrete_sequence=PALETTE,
                      labels={"date": "Ngày", "energy_kwh": "kWh/ngày", "branch": "Nhánh đo"})
        plot(fig, 370)
    note("Sub-metering đo điện năng theo phút ở đơn vị Wh, đã chuyển sang kWh bằng cách chia 1000. "
         "Phần 'Chưa phân nhánh' = điện năng toàn hộ trừ ba nhánh; "
         "không phải phép đo riêng của một thiết bị thứ tư.")
    section("Giả lập kịch bản", "Nếu giảm mức tiêu thụ từ dữ liệu đã ghi nhận")
    share = st.slider("Mức giảm giả định", min_value=5, max_value=30, value=10, step=5,
                      format="%d%%", key="device_scenario")
    m1, m2, m3 = st.columns(3)
    saving = full_total * share / 100
    m1.metric("Điện năng quan sát", f"{format_number(full_total, 1)} kWh")
    m2.metric("Tiết kiệm giả định", f"{format_number(saving, 1)} kWh")
    m3.metric("Điện năng còn lại", f"{format_number(full_total - saving, 1)} kWh")
    st.caption("Đây là phép nhân kịch bản minh họa, KHÔNG phải bảo đảm tiết kiệm và KHÔNG phải dự báo AI.")
