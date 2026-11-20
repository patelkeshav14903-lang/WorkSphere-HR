"""
WorkSphere HR - Smart HR & Project Management Dashboard
Main application entry point orchestrating modular views, state, and database initialization.
"""

import streamlit as st
import os

# 1. Page Configuration (must be called first)
st.set_page_config(
    page_title="WorkSphere HR & Project Hub",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Database Auto-Initialization & Seeding
from db.connection import init_db
from db.seed import seed_database
from utils.ui_helpers import apply_custom_theme
from config import APP_NAME, APP_TAGLINE, APP_ICON, DATABASE_URL

# Apply custom enterprise CSS styling
apply_custom_theme()


@st.cache_resource
def bootstrap_database():
    """Ensure database tables exist and realistic seed data is available out-of-the-box."""
    init_db()
    seed_database(force_reseed=False)
    return True


bootstrap_database()

# 3. Import View Modules
from views.dashboard_view import render_dashboard_view
from views.employees_view import render_employees_view
from views.attendance_view import render_attendance_view
from views.leave_view import render_leave_view
from views.payroll_view import render_payroll_view
from views.projects_view import render_projects_view

# 4. Session State Initialization
if "privacy_masked" not in st.session_state:
    st.session_state.privacy_masked = False

if "nav_section" not in st.session_state:
    st.session_state.nav_section = "📊 Dashboard Overview"

# 5. Sidebar Navigation & Global Controls
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_NAME}")
    st.caption(APP_TAGLINE)
    st.markdown("---")

    nav_options = [
        "📊 Dashboard Overview",
        "👥 Employee Directory",
        "⏱️ Attendance & Time",
        "🏖️ Leave Management",
        "💳 Payroll & Compensation",
        "🚀 Projects & Workloads",
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=nav_options.index(st.session_state.nav_section) if st.session_state.nav_section in nav_options else 0,
        label_visibility="collapsed",
    )
    st.session_state.nav_section = selected_nav

    st.markdown("---")
    st.markdown("### 🔐 Security & Controls")

    privacy_toggle = st.toggle(
        "🔒 Mask Payroll Figures",
        value=st.session_state.privacy_masked,
        help="Masks sensitive compensation, bonus, deduction, and salary amounts throughout the app.",
    )
    if privacy_toggle != st.session_state.privacy_masked:
        st.session_state.privacy_masked = privacy_toggle
        st.rerun()

    st.markdown("---")
    st.markdown("### 🗄️ Database Info")
    db_engine_name = "PostgreSQL" if "postgresql" in DATABASE_URL.lower() else "SQLite"
    st.caption(f"**Engine**: `{db_engine_name}`")
    st.caption(f"**Connection**: `{DATABASE_URL[:25]}...`")

    with st.expander("🛠️ Maintenance & Reset", expanded=False):
        if st.button("🔄 Reset to Demo Seed Data", use_container_width=True):
            seed_database(force_reseed=True)
            st.toast("Database reset to demo state!", icon="✅")
            st.rerun()

    st.markdown("---")
    st.caption("WorkSphere HR v2.4 • Enterprise Edition")

# 6. View Routing
if st.session_state.nav_section == "📊 Dashboard Overview":
    render_dashboard_view()
elif st.session_state.nav_section == "👥 Employee Directory":
    render_employees_view()
elif st.session_state.nav_section == "⏱️ Attendance & Time":
    render_attendance_view()
elif st.session_state.nav_section == "🏖️ Leave Management":
    render_leave_view()
elif st.session_state.nav_section == "💳 Payroll & Compensation":
    render_payroll_view()
elif st.session_state.nav_section == "🚀 Projects & Workloads":
    render_projects_view()
