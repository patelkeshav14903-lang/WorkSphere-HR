"""
WorkSphere HR - Attendance Module View
Daily check-in/out logging, real-time status tracking, historical audits,
and monthly aggregated summaries.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from services.attendance_service import (
    log_attendance,
    get_today_attendance,
    get_attendance_history,
    get_monthly_attendance_summary,
    get_attendance_kpis,
)
from services.employee_service import get_all_employees, get_all_departments
from utils.ui_helpers import render_kpi_card, render_badge


def render_attendance_view():
    st.title("⏱️ Attendance & Time Tracking")
    st.caption("Monitor daily workforce presence, log check-in/out stamps, and audit monthly attendance summaries.")

    tab_daily, tab_history, tab_monthly = st.tabs([
        "📍 Daily Check-In / Logger",
        "📜 Attendance History & Logs",
        "📊 Monthly Attendance Summary",
    ])

    # Fetch active employees for selectboxes
    employees = get_all_employees(active_only=True)
    emp_map = {e["id"]: f"{e['full_name']} ({e['emp_code']} - {e['role']})" for e in employees}
    departments = get_all_departments()

    # -------------------------------------------------------------
    # TAB 1: DAILY CHECK-IN & TODAY'S ATTENDANCE
    # -------------------------------------------------------------
    with tab_daily:
        # Today's KPI banner
        kpis = get_attendance_kpis(target_date=date.today())
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            render_kpi_card("Present (On-site)", str(kpis["present_count"]), "At Office", "🏢")
        with k2:
            render_kpi_card("Remote (WFH)", str(kpis["remote_count"]), "Working from home", "💻")
        with k3:
            render_kpi_card("Late Arrivals", str(kpis["late_count"]), "After 09:30 AM", "⚠️")
        with k4:
            render_kpi_card("Unplanned Absent", str(kpis["absent_count"]), "No check-in", "❌")
        with k5:
            render_kpi_card("Attendance Rate", f"{kpis['attendance_rate']}%", f"{kpis['total_working']}/{kpis['total_active_employees']} Staff", "📈")

        st.markdown("---")

        col_form, col_live = st.columns([1.2, 1.8])

        with col_form:
            st.subheader("📝 Log Attendance Record")
            with st.form("log_attendance_form"):
                emp_id = st.selectbox(
                    "Employee *",
                    options=list(emp_map.keys()),
                    format_func=lambda x: emp_map[x],
                )
                log_dt = st.date_input("Date *", value=date.today())
                status = st.selectbox(
                    "Status *",
                    options=["Present", "Remote", "Late", "Absent", "On Leave"],
                    index=0,
                )
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    cin = st.text_input("Check-In Time", value="09:00", placeholder="HH:MM e.g. 09:15")
                with col_t2:
                    cout = st.text_input("Check-Out Time", value="18:00", placeholder="HH:MM e.g. 18:00")

                notes = st.text_input("Remarks / Reason", placeholder="e.g. Approved remote work / Biometric sync")
                submit_log = st.form_submit_button("💾 Save Attendance Entry", type="primary", use_container_width=True)

                if submit_log:
                    # Sanitize times for Absent
                    if status == "Absent":
                        cin, cout = None, None
                    success, msg = log_attendance(
                        employee_id=emp_id,
                        log_date=log_dt,
                        check_in=cin if cin else None,
                        check_out=cout if cout else None,
                        status=status,
                        notes=notes,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with col_live:
            st.subheader("📅 Today's Attendance Roster")
            today_records = get_today_attendance(filter_date=date.today())
            if today_records:
                display_recs = []
                for r in today_records:
                    display_recs.append({
                        "Code": r["emp_code"],
                        "Employee": r["employee_name"],
                        "Department": r["department"],
                        "Check In": r["check_in"],
                        "Check Out": r["check_out"],
                        "Hours": f"{r['working_hours']} hrs" if r["working_hours"] > 0 else "--",
                        "Status": r["status"],
                        "Notes": r["notes"],
                    })
                df_today = pd.DataFrame(display_recs)
                st.dataframe(df_today, use_container_width=True, hide_index=True)
            else:
                st.info("No attendance entries found for today yet.")

    # -------------------------------------------------------------
    # TAB 2: ATTENDANCE HISTORY & AUDIT
    # -------------------------------------------------------------
    with tab_history:
        st.subheader("🔍 Historical Attendance Query")
        h_col1, h_col2, h_col3, h_col4 = st.columns(4)

        with h_col1:
            date_range = st.date_input(
                "Date Window",
                value=(date.today() - timedelta(days=14), date.today()),
                key="att_history_range",
            )
        with h_col2:
            h_dept = st.selectbox(
                "Filter by Department",
                ["All Departments"] + [d["name"] for d in departments],
                key="att_hist_dept",
            )
            dept_id_filter = next((d["id"] for d in departments if d["name"] == h_dept), None) if h_dept != "All Departments" else None
        with h_col3:
            h_emp_opts = [None] + list(emp_map.keys())
            h_emp = st.selectbox(
                "Filter by Employee",
                options=h_emp_opts,
                format_func=lambda x: "All Employees" if x is None else emp_map[x],
                key="att_hist_emp",
            )
        with h_col4:
            h_status = st.selectbox(
                "Filter by Status",
                ["All", "Present", "Remote", "Late", "Absent", "On Leave"],
                key="att_hist_status",
            )

        start_d = date_range[0] if isinstance(date_range, tuple) and len(date_range) >= 1 else None
        end_d = date_range[1] if isinstance(date_range, tuple) and len(date_range) >= 2 else start_d

        hist_records = get_attendance_history(
            start_date=start_d,
            end_date=end_d,
            employee_id=h_emp,
            department_id=dept_id_filter,
            status_filter=h_status,
        )

        st.caption(f"Showing {len(hist_records)} attendance logs")
        if hist_records:
            h_df = pd.DataFrame(hist_records)
            h_df = h_df[["date", "emp_code", "employee_name", "department", "status", "check_in", "check_out", "working_hours", "notes"]]
            h_df.columns = ["Date", "Emp Code", "Employee Name", "Department", "Status", "Check In", "Check Out", "Working Hours", "Notes"]
            st.dataframe(h_df, use_container_width=True, hide_index=True)
        else:
            st.info("No attendance records found matching these criteria.")

    # -------------------------------------------------------------
    # TAB 3: MONTHLY ATTENDANCE SUMMARY
    # -------------------------------------------------------------
    with tab_monthly:
        st.subheader("📊 Monthly Consolidated Attendance")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            sel_year = st.selectbox("Year", [2026, 2025, 2024], index=0, key="att_month_yr")
        with m_col2:
            sel_month = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                index=10,  # November (month 11)
                format_func=lambda m: datetime(2026, m, 1).strftime("%B"),
                key="att_month_mth",
            )

        monthly_summary = get_monthly_attendance_summary(year=sel_year, month=sel_month)
        if monthly_summary:
            m_df = pd.DataFrame(monthly_summary)
            display_m_df = m_df[[
                "emp_code", "employee_name", "department",
                "total_logged_days", "present_days", "remote_days", "late_days", "absent_days",
                "total_hours", "attendance_rate"
            ]]
            display_m_df.columns = [
                "Emp Code", "Employee", "Department",
                "Logged Days", "Present", "Remote", "Late", "Absent",
                "Total Hours", "Attendance Rate (%)"
            ]
            st.dataframe(
                display_m_df.style.format({
                    "Total Hours": "{:.1f}",
                    "Attendance Rate (%)": "{:.1f}%",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No attendance records found for the selected month.")
