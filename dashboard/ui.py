"""Shared Streamlit + Plotly design primitives."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

TEAL = "#07848A"
INK = "#19364B"
BLUE = "#4975B7"
GOLD = "#D7A343"
CORAL = "#E47768"
PURPLE = "#8263B9"
PALETTE = [TEAL, BLUE, GOLD, PURPLE, CORAL]


def style(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=16, r=16, t=35, b=16),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color=INK),
        hovermode="x unified", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#E5ECF2"),
        yaxis=dict(showgrid=True, gridcolor="#EFF3F6", zeroline=False),
    )
    return fig


def plot(fig: go.Figure, height: int = 340) -> None:
    st.plotly_chart(
        style(fig, height), use_container_width=True,
        config={"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 2}},
    )


def section(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="eyebrow">{kicker}</div>', unsafe_allow_html=True)
    st.subheader(title)
    if subtitle:
        st.markdown(f'<p class="lead">{subtitle}</p>', unsafe_allow_html=True)


def note(message: str) -> None:
    st.markdown(f'<div class="note">{message}</div>', unsafe_allow_html=True)
