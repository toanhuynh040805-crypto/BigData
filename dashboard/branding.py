"""Small, inline SVG product brand elements. Static icons, no font dependency."""
from __future__ import annotations

ICONS = {
    "bolt": '<path d="m13 2-3 8H5l7 12 2-8h5L13 2Z"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-7"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    "activity": '<path d="M22 12h-4l-3 9-6-18-3 9H2"/>',
}


def icon(name: str, size: int = 22, color: str = "currentColor") -> str:
    if name not in ICONS:
        raise ValueError(f"Unsupported icon: {name}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="1.85" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        f'{ICONS[name]}</svg>'
    )


def sidebar_brand() -> str:
    return (
        '<div class="sidebar-brand">'
        '<div class="brand-mark">' + icon("bolt", 25, "#FFFFFF") + '</div>'
        '<div><div class="brand-name">ENERGY<span>IQ</span></div>'
        '<div class="brand-subtitle">INTELLIGENCE PLATFORM</div></div>'
        '</div>'
        '<div class="brand-division">CAPSTONE · BIG DATA ANALYTICS</div>'
    )


def hero_header(clean_rows: int, first: str, last: str, is_uci: bool) -> str:
    provenance = "BỘ DỮ LIỆU UCI THẬT" if is_uci else "KIỂM TRA NGUỒN DỮ LIỆU"
    return (
        '<div class="hero">'
        '<div class="hero-copy">'
        '<div class="hero-eyebrow"><span class="hero-eyebrow-dot"></span> '
        'BIG DATA / ELECTRICITY ANALYTICS</div>'
        '<h1>Nền tảng phân tích<br><span>điện năng thông minh</span></h1>'
        '<p>Khám phá hành vi tiêu thụ, xác định xu hướng và đánh giá dự báo điện năng '
        'bằng Apache Spark &amp; Random Forest — từ dữ liệu lịch sử có thể kiểm chứng.</p>'
        '<div class="hero-tags"><span>APACHE SPARK</span><span>RANDOM FOREST</span>'
        '<span>UCI DATASET</span><span>STREAMLIT</span></div>'
        '</div>'
        '<div class="hero-visual">'
        '<div class="hero-orbit hero-orbit-one"></div><div class="hero-orbit hero-orbit-two"></div>'
        '<div class="hero-topline">' + icon("activity", 18, "#9BDFF0") + ' LIVE DATA SNAPSHOT</div>'
        '<div class="hero-large-value">' + f"{clean_rows / 1_000_000:.2f}" + '<small>M</small></div>'
        '<div class="hero-visual-caption">BẢN GHI HỢP LỆ</div>'
        '<svg class="hero-wave" viewBox="0 0 260 68" preserveAspectRatio="none" aria-hidden="true">'
        '<defs><linearGradient id="sparkFill" x1="0" x2="0" y1="0" y2="1">'
        '<stop offset="0%" stop-color="#53D4DC" stop-opacity=".35"/>'
        '<stop offset="100%" stop-color="#53D4DC" stop-opacity="0"/></linearGradient></defs>'
        '<path d="M0 54 L20 49 L40 55 L60 34 L80 40 L100 19 L120 37 L140 24 '
        'L160 32 L180 12 L200 22 L220 8 L240 20 L260 4 L260 68 L0 68Z" fill="url(#sparkFill)"/>'
        '<path d="M0 54 L20 49 L40 55 L60 34 L80 40 L100 19 L120 37 L140 24 '
        'L160 32 L180 12 L200 22 L220 8 L240 20 L260 4" stroke="#71E5E5" '
        'stroke-width="2.5" stroke-linejoin="round" fill="none"/></svg>'
        '<div class="hero-visual-bottom">' + icon("calendar", 14, "#95B9CC") +
        f'<span>{first} – {last}</span></div>'
        '</div></div>'
        f'<div class="source-banner"><span class="source-symbol">{icon("shield", 18, "#047D84")}</span>'
        '<div><strong>' + provenance + '</strong><span> · '
        'Dữ liệu một hộ gia đình ở Pháp (2006–2010). Kết quả lịch sử, không phải thời gian thực.'
        '</span></div></div>'
    )


def sidebar_data_badge() -> str:
    return (
        '<div class="sidebar-badge">'
        '<div class="sidebar-badge-icon">' + icon("database", 19, "#0F8F92") + '</div>'
        '<div><div class="sidebar-badge-title">Historical Dataset</div>'
        '<div class="sidebar-badge-text">UCI · 2006–2010 · 1 hộ gia đình</div></div>'
        '<span class="sidebar-badge-dot"></span>'
        '</div>'
    )
