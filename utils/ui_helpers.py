"""
WorkSphere HR - UI Helper Utilities
Custom CSS styling, metrics formatting, badge generators, and privacy masking.
"""

import streamlit as st
from config import CURRENCY_SYMBOL


def apply_custom_theme():
    """Inject polished enterprise styling."""
    st.markdown(
        """
        <style>
            /* Main container polish */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1300px;
            }
            
            /* Metric Card styling */
            .ws-kpi-card {
                background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 18px 20px;
                margin-bottom: 12px;
                box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
                transition: transform 0.15s ease, box-shadow 0.15s ease;
            }
            .ws-kpi-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
            }
            .ws-kpi-title {
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: #64748b;
                font-weight: 600;
                margin-bottom: 4px;
            }
            .ws-kpi-value {
                font-size: 1.75rem;
                font-weight: 700;
                color: #0f172a;
                line-height: 1.2;
            }
            .ws-kpi-subtitle {
                font-size: 0.8rem;
                color: #94a3b8;
                margin-top: 4px;
            }

            /* Badge pill classes */
            .ws-badge {
                display: inline-block;
                padding: 4px 10px;
                font-size: 0.78rem;
                font-weight: 600;
                border-radius: 9999px;
                text-align: center;
                letter-spacing: 0.02em;
            }
            .badge-success { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
            .badge-info { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
            .badge-warning { background-color: #fef9c3; color: #a16207; border: 1px solid #fef08a; }
            .badge-danger { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
            .badge-secondary { background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
            .badge-purple { background-color: #f3e8ff; color: #7e22ce; border: 1px solid #e9d5ff; }

            /* Project & Employee Cards */
            .ws-record-card {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 16px;
                margin-bottom: 12px;
                box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_currency(amount: float, symbol: str = CURRENCY_SYMBOL) -> str:
    """Format floating point numbers to currency strings."""
    try:
        return f"{symbol} {float(amount):,.2f}"
    except (ValueError, TypeError):
        return f"{symbol} 0.00"


def mask_currency(amount: float, is_masked: bool = False, symbol: str = CURRENCY_SYMBOL) -> str:
    """
    Format currency with privacy toggle.
    If is_masked is True, returns masked string '••••••'.
    """
    if is_masked:
        return f"{symbol} ••••••"
    return format_currency(amount, symbol)


def render_badge(text: str, badge_type: str = "secondary") -> str:
    """Generate HTML badge string."""
    type_map = {
        # General
        "success": "badge-success",
        "info": "badge-info",
        "warning": "badge-warning",
        "danger": "badge-danger",
        "secondary": "badge-secondary",
        "purple": "badge-purple",
        # Attendance & Statuses
        "Present": "badge-success",
        "Remote": "badge-info",
        "Late": "badge-warning",
        "Absent": "badge-danger",
        "On Leave": "badge-purple",
        # Leaves
        "Approved": "badge-success",
        "Pending": "badge-warning",
        "Rejected": "badge-danger",
        # Tasks & Projects
        "Done": "badge-success",
        "Completed": "badge-success",
        "In Progress": "badge-info",
        "To Do": "badge-secondary",
        "Planning": "badge-secondary",
        "Blocked": "badge-danger",
        "On Hold": "badge-warning",
        # Priority
        "Critical": "badge-danger",
        "High": "badge-warning",
        "Medium": "badge-info",
        "Low": "badge-secondary",
    }
    css_class = type_map.get(badge_type, type_map.get(text, "badge-secondary"))
    return f'<span class="ws-badge {css_class}">{text}</span>'


def render_kpi_card(title: str, value: str, subtitle: str = "", icon: str = ""):
    """Render a styled KPI widget."""
    icon_html = f"<span style='float:right; font-size:1.3rem; opacity:0.8;'>{icon}</span>" if icon else ""
    st.markdown(
        f"""
        <div class="ws-kpi-card">
            {icon_html}
            <div class="ws-kpi-title">{title}</div>
            <div class="ws-kpi-value">{value}</div>
            <div class="ws-kpi-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
