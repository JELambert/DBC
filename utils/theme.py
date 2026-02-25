"""Color palette, member colors, and CSS for the DBC dashboard."""

# Wine/book-club themed palette
COLORS = {
    "primary": "#722F37",       # wine red
    "secondary": "#C9A96E",     # gold
    "accent": "#2E4057",        # navy
    "bg_dark": "#1A1A2E",       # dark background
    "bg_card": "#16213E",       # card background
    "text": "#FAFAFA",          # light text
    "text_muted": "#A0A0B0",    # muted text
    "success": "#2A9D8F",       # green
    "danger": "#E63946",        # red
    "warning": "#E9C46A",       # yellow
}

# Consistent member colors across all charts
MEMBER_COLORS = {
    "Willy": "#E63946",
    "Bartel": "#457B9D",
    "Josh": "#2A9D8F",
    "Faulkner": "#E9C46A",
    "Ryan": "#F4A261",
    "John": "#264653",
    "Christian": "#7B2D8E",
}

MEMBERS = list(MEMBER_COLORS.keys())

# Plotly layout defaults
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Georgia, serif", color=COLORS["text"], size=13),
    margin=dict(l=40, r=40, t=50, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.1)"),
)


def apply_plotly_theme(fig):
    """Apply the DBC wine theme to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


def metric_card_css():
    """Return CSS for styled metric cards."""
    return """
    <style>
    [data-testid="stMetric"] {
        background-color: #16213E;
        border: 1px solid #722F37;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 12px rgba(114, 47, 55, 0.2);
    }
    [data-testid="stMetricLabel"] {
        color: #C9A96E;
        font-family: Georgia, serif;
        font-size: 0.85rem;
    }
    [data-testid="stMetricValue"] {
        color: #FAFAFA;
        font-family: Georgia, serif;
    }
    </style>
    """


def page_header(title, subtitle=""):
    """Return styled HTML for a page header."""
    sub = f'<p style="color: {COLORS["text_muted"]}; font-size: 1rem; margin-top: 4px;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin-bottom: 1.5rem;">
        <h1 style="font-family: Georgia, serif; color: {COLORS["secondary"]}; margin-bottom: 0;">{title}</h1>
        {sub}
    </div>
    """


def award_card(emoji, title, winner, detail=""):
    """Return styled HTML for an award card."""
    detail_html = f'<p style="color: {COLORS["text_muted"]}; font-size: 0.8rem; margin: 4px 0 0 0;">{detail}</p>' if detail else ""
    return f"""
    <div style="background: {COLORS["bg_card"]}; border: 1px solid {COLORS["primary"]};
                border-radius: 12px; padding: 20px; text-align: center;
                box-shadow: 0 4px 12px rgba(114, 47, 55, 0.15);">
        <div style="font-size: 2.5rem; margin-bottom: 8px;">{emoji}</div>
        <div style="color: {COLORS["secondary"]}; font-family: Georgia, serif;
                    font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">{title}</div>
        <div style="color: {COLORS["text"]}; font-family: Georgia, serif;
                    font-size: 1.2rem; font-weight: bold; margin-top: 6px;">{winner}</div>
        {detail_html}
    </div>
    """


def stat_card(label, value, color=None):
    """Return styled HTML for a stat/trivia card."""
    border_color = color or COLORS["primary"]
    return f"""
    <div style="background: {COLORS["bg_card"]}; border-left: 4px solid {border_color};
                border-radius: 8px; padding: 16px 20px; margin-bottom: 12px;">
        <div style="color: {COLORS["text_muted"]}; font-size: 0.8rem; text-transform: uppercase;
                    letter-spacing: 0.5px;">{label}</div>
        <div style="color: {COLORS["text"]}; font-size: 1.4rem; font-weight: bold;
                    font-family: Georgia, serif; margin-top: 4px;">{value}</div>
    </div>
    """
