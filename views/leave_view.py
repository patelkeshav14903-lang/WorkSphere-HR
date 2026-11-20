"""
WorkSphere HR - Leave Management Module View
Leave balance tracking by category, request submission, approval/rejection workflows,
and team calendar timeline.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from services.leave_service import (
    get_employee_leave_balance,
    get_all_leave_balances,
    submit_leave_request,
    review_leave_request,
    get_leave_requests,
    get_team_leave_calendar,
    get_leave_kpis,
)
from services.employee_service import get_all_employees, get_all_departments
from utils.ui_helpers import render_kpi_card, render_badge


def render_leave_view():
    st.title("🏖️ Leave Records & Request Workflow")
    st.caption("Manage employee leave balances, submit PTO applications, review team requests, and view the team absence schedule.")

    tab_balances, tab_submit, tab_workflow, tab_calendar = st.tabs([
        "💼 Quotas & Balances",
        "📝 Submit Leave Request",
        "⚖️ Approval / Rejection Workflow",
        "📅 Team Leave Schedule",
    ])

    employees = get_all_employees(active_only=True)
    emp_map = {e["id"]: f"{e['full_name']} ({e['emp_code']})" for e in employees}
    departments = get_all_departments()

    # -------------------------------------------------------------
    # TAB 1: LEAVE BALANCES
    # -------------------------------------------------------------
    with tab_balances:
        st.subheader("📊 Annual Leave Balances (2026)")
        kpis = get_leave_kpis()
        c1, c2, c3 = st.columns(3)
        with c1:
            render_kpi_card("Pending Requests", str(kpis["pending_count"]), "Awaiting approval", "⏳")
        with c2:
            render_kpi_card("Approved Requests", str(kpis["approved_count"]), "Confirmed time-off", "✅")
        with c3:
            render_kpi_card("Staff on Leave Today", str(kpis["on_leave_today_count"]), "Currently out of office", "🌴")

        st.markdown("---")
        balances = get_all_leave_balances(year=2026)
        if balances:
            b_df = pd.DataFrame(balances)
            display_b_df = b_df[[
                "emp_code", "employee_name", "department",
                "casual_total", "casual_used", "casual_remaining",
                "sick_total", "sick_used", "sick_remaining",
                "earned_total", "earned_used", "earned_remaining",
                "total_remaining",
            ]]
            display_b_df.columns = [
                "Emp Code", "Employee", "Department",
                "Casual Total", "Casual Used", "Casual Left",
                "Sick Total", "Sick Used", "Sick Left",
                "Earned Total", "Earned Used", "Earned Left",
                "Total Remaining",
            ]
            st.dataframe(display_b_df, use_container_width=True, hide_index=True)
        else:
            st.info("No leave balance records found.")

    # -------------------------------------------------------------
    # TAB 2: SUBMIT LEAVE REQUEST
    # -------------------------------------------------------------
    with tab_submit:
        st.subheader("📝 Request Time Off")
        st.caption("Apply for Casual, Sick, or Earned Leave. Quota availability is checked automatically.")

        sub_col_form, sub_col_info = st.columns([1.5, 1])

        with sub_col_form:
            with st.form("submit_leave_form"):
                sel_emp_id = st.selectbox(
                    "Employee Requesting Leave *",
                    options=list(emp_map.keys()),
                    format_func=lambda x: emp_map[x],
                    key="leave_submit_emp",
                )
                leave_type = st.selectbox(
                    "Leave Category *",
                    ["Casual", "Sick", "Earned"],
                    key="leave_submit_type",
                )
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    start_date = st.date_input("Start Date *", value=date.today() + timedelta(days=1), key="leave_start_dt")
                with col_d2:
                    end_date = st.date_input("End Date *", value=date.today() + timedelta(days=2), key="leave_end_dt")

                reason = st.text_area(
                    "Reason for Absence *",
                    placeholder="Provide context for manager approval...",
                    key="leave_reason_txt",
                )

                submit_btn = st.form_submit_button("🚀 Submit Leave Request", type="primary", use_container_width=True)

                if submit_btn:
                    success, msg, req_id = submit_leave_request(
                        employee_id=sel_emp_id,
                        leave_type=leave_type,
                        start_date=start_date,
                        end_date=end_date,
                        reason=reason,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Request Rejected: {msg}")

        with sub_col_info:
            st.subheader("💡 Balance Quick Check")
            if sel_emp_id:
                emp_bal = get_employee_leave_balance(sel_emp_id, year=2026)
                st.markdown(f"**Year {emp_bal['year']} Quotas:**")
                st.markdown(f"• **Casual Leave**: **{emp_bal['casual']['remaining']}** days remaining (Used: {emp_bal['casual']['used']})")
                st.markdown(f"• **Sick Leave**: **{emp_bal['sick']['remaining']}** days remaining (Used: {emp_bal['sick']['used']})")
                st.markdown(f"• **Earned Leave**: **{emp_bal['earned']['remaining']}** days remaining (Used: {emp_bal['earned']['used']})")
                st.markdown(f"• **Total Available**: **{emp_bal['total_remaining']}** days")

    # -------------------------------------------------------------
    # TAB 3: APPROVAL / REJECTION WORKFLOW
    # -------------------------------------------------------------
    with tab_workflow:
        st.subheader("⚖️ Manager & HR Review Workflow")
        st.caption("Review pending requests. Approving will automatically deduct the balance.")

        pending_requests = get_leave_requests(status_filter="Pending")

        if pending_requests:
            st.markdown(f"Found **{len(pending_requests)}** pending request(s) awaiting decision:")
            for req in pending_requests:
                with st.expander(
                    f"🔔 **{req['employee_name']}** — {req['leave_type']} Leave ({int(req['days_requested'])} days: {req['start_date']} to {req['end_date']})",
                    expanded=True,
                ):
                    r_col1, r_col2 = st.columns([2, 1.5])
                    with r_col1:
                        st.markdown(f"**Employee**: `{req['employee_name']} ({req['emp_code']})`")
                        st.markdown(f"**Department**: `{req['department']}`")
                        st.markdown(f"**Leave Category**: `{req['leave_type']}`")
                        st.markdown(f"**Dates**: `{req['start_date']}` to `{req['end_date']}` (**{int(req['days_requested'])} working days**)")
                        st.markdown(f"**Reason**: *\"{req['reason']}\"*")

                    with r_col2:
                        with st.form(f"review_form_{req['id']}"):
                            reviewer_id = st.selectbox(
                                "Reviewer Account *",
                                options=list(emp_map.keys()),
                                format_func=lambda x: emp_map[x],
                                key=f"rev_sel_{req['id']}",
                            )
                            comments = st.text_input("Review Comments", placeholder="e.g. Approved. Sprint work covered.", key=f"rev_notes_{req['id']}")
                            b_col1, b_col2 = st.columns(2)
                            with b_col1:
                                approve_btn = st.form_submit_button("✅ Approve", type="primary", use_container_width=True)
                            with b_col2:
                                reject_btn = st.form_submit_button("❌ Reject", use_container_width=True)

                            if approve_btn:
                                success, msg = review_leave_request(
                                    request_id=req["id"],
                                    reviewer_id=reviewer_id,
                                    action="Approved",
                                    comments=comments,
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

                            if reject_btn:
                                success, msg = review_leave_request(
                                    request_id=req["id"],
                                    reviewer_id=reviewer_id,
                                    action="Rejected",
                                    comments=comments,
                                )
                                if success:
                                    st.warning(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
        else:
            st.success("🎉 All leave requests have been reviewed! No pending requests.")

        st.markdown("---")
        st.subheader("📜 Complete Request History")
        all_reqs = get_leave_requests()
        if all_reqs:
            clean_reqs = []
            for r in all_reqs:
                clean_reqs.append({
                    "ID": r["id"],
                    "Employee": r["employee_name"],
                    "Type": r["leave_type"],
                    "Start": str(r["start_date"]),
                    "End": str(r["end_date"]),
                    "Days": int(r["days_requested"]),
                    "Status": r["status"],
                    "Reviewer": r["reviewer_name"],
                    "Comments": r["review_notes"],
                })
            st.dataframe(pd.DataFrame(clean_reqs), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # TAB 4: TEAM LEAVE SCHEDULE / CALENDAR
    # -------------------------------------------------------------
    with tab_calendar:
        st.subheader("📅 Team Leave Calendar & Availability Schedule")
        cal_col1, cal_col2 = st.columns(2)
        with cal_col1:
            cal_start = st.date_input("From Date", value=date.today() - timedelta(days=7), key="cal_start")
        with cal_col2:
            cal_end = st.date_input("To Date", value=date.today() + timedelta(days=30), key="cal_end")

        team_leaves = get_team_leave_calendar(start_date=cal_start, end_date=cal_end)
        if team_leaves:
            cal_df = pd.DataFrame(team_leaves)
            cal_df = cal_df[["employee_name", "department", "leave_type", "start_date", "end_date", "days", "status", "reason"]]
            cal_df.columns = ["Employee", "Department", "Leave Type", "Start Date", "End Date", "Working Days", "Status", "Reason"]
            st.dataframe(cal_df, use_container_width=True, hide_index=True)
        else:
            st.info("No approved or pending team absences scheduled in this timeframe.")
