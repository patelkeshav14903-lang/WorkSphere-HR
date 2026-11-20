"""
WorkSphere HR - Executive Dashboard View
Comprehensive summary KPIs, live status tracking, and visual analytics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from services.employee_service import get_employee_stats, get_all_employees
from services.attendance_service import get_attendance_kpis
from services.leave_service import get_leave_kpis, get_leave_requests
from services.payroll_service import get_payroll_kpis
from services.project_service import get_project_kpis, get_all_projects, get_project_tasks
from utils.ui_helpers import render_kpi_card, mask_currency, render_badge
from config import CURRENCY_SYMBOL


def render_dashboard_view():
    st.title("📊 Executive Operations Dashboard")
    st.caption("Live pulse of company workforce, operational attendance, leave pipeline, and active project deliverables.")

    # 1. Fetch aggregated stats
    emp_stats = get_employee_stats()
    att_kpis = get_attendance_kpis()
    leave_kpis = get_leave_kpis()
    payroll_kpis = get_payroll_kpis()
    proj_kpis = get_project_kpis()

    is_masked = st.session_state.get("privacy_masked", False)

    # 2. Executive KPI Cards Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
    with kpi_col1:
        render_kpi_card(
            title="Total Workforce",
            value=str(emp_stats["active_employees"]),
            subtitle=f"{emp_stats['completed_onboarding']} Onboarded",
            icon="👥",
        )
    with kpi_col2:
        render_kpi_card(
            title="Today's Attendance",
            value=f"{att_kpis['attendance_rate']}%",
            subtitle=f"{att_kpis['total_working']} Working ({att_kpis['present_count']} On-site, {att_kpis['remote_count']} Remote)",
            icon="⏱️",
        )
    with kpi_col3:
        render_kpi_card(
            title="Pending Leaves",
            value=str(leave_kpis["pending_count"]),
            subtitle=f"{leave_kpis['on_leave_today_count']} On Leave Today",
            icon="🏖️",
        )
    with kpi_col4:
        render_kpi_card(
            title="Active Projects",
            value=str(proj_kpis["active_projects"]),
            subtitle=f"{proj_kpis['overall_completion_rate']}% Completion Rate",
            icon="🚀",
        )
    with kpi_col5:
        monthly_cost_display = mask_currency(payroll_kpis["total_net"], is_masked=is_masked)
        render_kpi_card(
            title="Monthly Net Payroll",
            value=monthly_cost_display,
            subtitle="Masked" if is_masked else f"{payroll_kpis['employees_count']} Employees Disbursed",
            icon="💳",
        )

    st.markdown("---")

    # 3. Operational Highlights & Action Center
    if leave_kpis["pending_count"] > 0 or proj_kpis["blocked_tasks"] > 0:
        alert_col1, alert_col2 = st.columns(2)
        with alert_col1:
            if leave_kpis["pending_count"] > 0:
                st.warning(f"⚠️ **Action Required**: {leave_kpis['pending_count']} pending leave request(s) awaiting manager/HR approval.")
        with alert_col2:
            if proj_kpis["blocked_tasks"] > 0:
                st.error(f"🚨 **Blocker Alert**: {proj_kpis['blocked_tasks']} critical task(s) currently marked as **Blocked**.")

    # 4. Interactive Analytical Visualizations
    col_chart_left, col_chart_right = st.columns([1, 1])

    with col_chart_left:
        st.subheader("🏢 Department Distribution")
        dept_dist = emp_stats["department_distribution"]
        if dept_dist:
            dept_df = pd.DataFrame(list(dept_dist.items()), columns=["Department", "Headcount"])
            fig_dept = px.bar(
                dept_df,
                x="Department",
                y="Headcount",
                color="Headcount",
                color_continuous_scale="Blues",
                text="Headcount",
            )
            fig_dept.update_traces(textposition="outside")
            fig_dept.update_layout(
                xaxis_title="",
                yaxis_title="Employees",
                height=320,
                margin=dict(l=10, r=10, t=20, b=10),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_dept, use_container_width=True)

    with col_chart_right:
        st.subheader("📅 Attendance Snapshot (Today)")
        att_labels = ["Present (On-site)", "Remote", "Late", "Absent"]
        att_values = [
            att_kpis["present_count"],
            att_kpis["remote_count"],
            att_kpis["late_count"],
            att_kpis["absent_count"],
        ]
        # Only render if we have values
        if sum(att_values) > 0:
            fig_donut = go.Figure(
                data=[
                    go.Pie(
                        labels=att_labels,
                        values=att_values,
                        hole=0.55,
                        marker_colors=["#10b981", "#3b82f6", "#f59e0b", "#ef4444"],
                    )
                ]
            )
            fig_donut.update_layout(
                height=320,
                margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No attendance records logged for today yet.")

    # 5. Project Deliverables Progress & Task Status Breakdown
    proj_col_1, proj_col_2 = st.columns([3, 2])

    with proj_col_1:
        st.subheader("🚀 Project Deliverables & Health")
        projects = get_all_projects()
        if projects:
            proj_df = pd.DataFrame(projects)
            fig_proj = px.bar(
                proj_df,
                x="progress_pct",
                y="name",
                orientation="h",
                text="progress_pct",
                color="status",
                color_discrete_map={
                    "Completed": "#10b981",
                    "In Progress": "#3b82f6",
                    "Planning": "#94a3b8",
                    "On Hold": "#f59e0b",
                },
            )
            fig_proj.update_traces(texttemplate="%{text}%", textposition="inside")
            fig_proj.update_layout(
                xaxis_title="Completion Progress (%)",
                yaxis_title="",
                xaxis_range=[0, 100],
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                legend_title="Project Status",
            )
            st.plotly_chart(fig_proj, use_container_width=True)

    with proj_col_2:
        st.subheader("📋 Task Status Overview")
        tasks = get_project_tasks()
        if tasks:
            status_counts = pd.Series([t["status"] for t in tasks]).value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_tasks = px.pie(
                status_counts,
                names="Status",
                values="Count",
                color="Status",
                color_discrete_map={
                    "Done": "#10b981",
                    "In Progress": "#3b82f6",
                    "To Do": "#cbd5e1",
                    "Blocked": "#ef4444",
                },
            )
            fig_tasks.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_tasks, use_container_width=True)

    # 6. Quick Activity Tables
    st.subheader("🔔 Recent Leave Requests & Urgent Tasks")
    tab_leaves, tab_tasks = st.tabs(["Pending / Recent Leaves", "Active Tasks"])

    with tab_leaves:
        recent_leaves = get_leave_requests()[:5]
        if recent_leaves:
            clean_leaves_data = []
            for l in recent_leaves:
                clean_leaves_data.append({
                    "Employee": l["employee_name"],
                    "Department": l["department"],
                    "Leave Type": l["leave_type"],
                    "Dates": f"{l['start_date']} to {l['end_date']} ({int(l['days_requested'])} days)",
                    "Status": l["status"],
                    "Reason": l["reason"][:45] + "..." if len(l["reason"]) > 45 else l["reason"],
                })
            st.dataframe(pd.DataFrame(clean_leaves_data), use_container_width=True, hide_index=True)
        else:
            st.info("No leave requests found.")

    with tab_tasks:
        recent_tasks = [t for t in tasks if t["status"] in ["In Progress", "Blocked"]][:6]
        if recent_tasks:
            clean_tasks_data = []
            for t in recent_tasks:
                clean_tasks_data.append({
                    "Task": t["title"],
                    "Project": t["project_name"],
                    "Assignee": t["assignee_name"],
                    "Priority": t["priority"],
                    "Status": t["status"],
                    "Due Date": str(t["due_date"]),
                })
            st.dataframe(pd.DataFrame(clean_tasks_data), use_container_width=True, hide_index=True)
        else:
            st.info("No active in-progress or blocked tasks.")
