"""
WorkSphere HR - Project Management View
Projects portfolio cards, task & milestone tracker, workload capacity, and progress metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from services.project_service import (
    get_all_projects,
    get_project_by_id,
    create_project,
    get_project_tasks,
    create_task,
    update_task_status,
    get_project_metrics,
    get_workload_metrics,
    get_project_kpis,
)
from services.employee_service import get_all_employees
from utils.ui_helpers import render_kpi_card, render_badge, format_currency
from config import CURRENCY_SYMBOL


def render_projects_view():
    st.title("🚀 Project & Workload Management")
    st.caption("Coordinate project milestones, track task completion lifecycle, assign deliverables, and balance staff workloads.")

    tab_portfolio, tab_tasks, tab_workload, tab_new_proj = st.tabs([
        "📁 Projects Portfolio",
        "📋 Tasks & Milestones Board",
        "⚖️ Team Workload Analytics",
        "➕ New Project & Task",
    ])

    employees = get_all_employees(active_only=True)
    emp_map = {e["id"]: f"{e['full_name']} ({e['role']})" for e in employees}
    projects = get_all_projects()
    proj_map = {p["id"]: f"{p['name']} ({p['code']})" for p in projects}

    # -------------------------------------------------------------
    # TAB 1: PROJECTS PORTFOLIO
    # -------------------------------------------------------------
    with tab_portfolio:
        # High level KPIs
        kpis = get_project_kpis()
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("Total Projects", str(kpis["total_projects"]), "Portfolio size", "📂")
        with c2:
            render_kpi_card("Active In Progress", str(kpis["active_projects"]), "Under active delivery", "⚡")
        with c3:
            render_kpi_card("Completion Rate", f"{kpis['overall_completion_rate']}%", f"{kpis['done_tasks']}/{kpis['total_tasks']} Tasks Completed", "🎯")
        with c4:
            render_kpi_card("Blocked Tasks", str(kpis["blocked_tasks"]), "Require intervention", "🚨")

        st.markdown("---")

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            status_f = st.selectbox("Filter Status", ["All", "In Progress", "Planning", "Completed", "On Hold"], key="proj_filter_st")
        with f_col2:
            prio_f = st.selectbox("Filter Priority", ["All", "Critical", "High", "Medium", "Low"], key="proj_filter_pr")

        filtered_projects = get_all_projects(status_filter=status_f, priority_filter=prio_f)

        if filtered_projects:
            for p in filtered_projects:
                with st.expander(f"**{p['code']}: {p['name']}** — {p['status']} ({p['progress_pct']}% Complete)", expanded=True):
                    col_p1, col_p2, col_p3 = st.columns([2.5, 2, 2])
                    with col_p1:
                        st.markdown(f"**Description**: {p['description']}")
                        st.markdown(f"• **Lead**: `{p['lead_name']}`")
                        st.markdown(f"• **Team Size**: `{p['member_count']} contributor(s)`")
                        st.markdown(f"• **Timeline**: `{p['start_date']}` to `{p['target_date']}`")

                    with col_p2:
                        st.markdown(f"• **Priority**: {render_badge(p['priority'], p['priority'])}", unsafe_allow_html=True)
                        st.markdown(f"• **Budget Allocation**: `{format_currency(p['budget'])}`")
                        st.markdown(f"• **Status**: {render_badge(p['status'], p['status'])}", unsafe_allow_html=True)

                    with col_p3:
                        st.markdown(f"**Progress**: `{p['progress_pct']}%`")
                        st.progress(min(1.0, p["progress_pct"] / 100.0))
                        st.caption(f"Done: {p['done_tasks']} | In Progress: {p['in_prog_tasks']} | Blocked: {p['blocked_tasks']} | To Do: {p['todo_tasks']}")

                    # Sub-tasks table for this project
                    proj_tasks = get_project_tasks(project_id=p["id"])
                    if proj_tasks:
                        st.markdown("**Milestones & Tasks:**")
                        t_summary = []
                        for t in proj_tasks:
                            t_summary.append({
                                "Title": t["title"],
                                "Milestone": t["milestone_name"],
                                "Assignee": t["assignee_name"],
                                "Priority": t["priority"],
                                "Status": t["status"],
                                "Due Date": str(t["due_date"]),
                                "Est. Hours": f"{t['estimated_hours']} hrs",
                            })
                        st.dataframe(pd.DataFrame(t_summary), use_container_width=True, hide_index=True)
                    else:
                        st.caption("No tasks created under this project yet.")
        else:
            st.info("No projects match the selected filters.")

    # -------------------------------------------------------------
    # TAB 2: TASKS & MILESTONES BOARD
    # -------------------------------------------------------------
    with tab_tasks:
        st.subheader("📋 Task Lifecycle Tracker")
        st.caption("Filter tasks, update live statuses (To Do, In Progress, Blocked, Done), and inspect assignees.")

        t_f1, t_f2, t_f3 = st.columns(3)
        with t_f1:
            t_proj_filter = st.selectbox(
                "Filter by Project",
                options=[None] + list(proj_map.keys()),
                format_func=lambda x: "All Projects" if x is None else proj_map[x],
                key="task_proj_sel",
            )
        with t_f2:
            t_stat_filter = st.selectbox("Status", ["All", "To Do", "In Progress", "Blocked", "Done"], key="task_stat_sel")
        with t_f3:
            t_prio_filter = st.selectbox("Priority", ["All", "Critical", "High", "Medium", "Low"], key="task_prio_sel")

        tasks_list = get_project_tasks(
            project_id=t_proj_filter,
            status_filter=t_stat_filter,
            priority_filter=t_prio_filter,
        )

        st.caption(f"Found {len(tasks_list)} task(s)")

        # Quick Status Transition tool
        if tasks_list:
            with st.expander("⚡ Quick Status Update Tool", expanded=False):
                with st.form("quick_status_form"):
                    qs_col1, qs_col2, qs_col3 = st.columns([2, 1.5, 1])
                    with qs_col1:
                        task_opts = {t["id"]: f"#{t['id']} [{t['status']}] {t['title']} ({t['project_code']})" for t in tasks_list}
                        sel_tid = st.selectbox("Select Task to Update", options=list(task_opts.keys()), format_func=lambda x: task_opts[x])
                    with qs_col2:
                        new_stat = st.selectbox("New Status", ["To Do", "In Progress", "Blocked", "Done"])
                    with qs_col3:
                        st.write("")
                        st.write("")
                        update_stat_btn = st.form_submit_button("Update Status", type="primary")

                    if update_stat_btn and sel_tid:
                        success, msg = update_task_status(sel_tid, new_stat)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)

            # Interactive task table
            t_display = []
            for t in tasks_list:
                t_display.append({
                    "ID": t["id"],
                    "Project": t["project_name"],
                    "Milestone": t["milestone_name"],
                    "Task Title": t["title"],
                    "Assignee": t["assignee_name"],
                    "Priority": t["priority"],
                    "Status": t["status"],
                    "Hours": t["estimated_hours"],
                    "Due Date": str(t["due_date"]),
                })
            st.dataframe(pd.DataFrame(t_display), use_container_width=True, hide_index=True)
        else:
            st.info("No tasks found matching current filters.")

    # -------------------------------------------------------------
    # TAB 3: WORKLOAD & RESOURCE CAPACITY
    # -------------------------------------------------------------
    with tab_workload:
        st.subheader("⚖️ Resource Workload & Capacity")
        st.caption("Distribution of open and completed deliverables across engineers and staff members.")

        workloads = get_workload_metrics()
        if workloads:
            w_df = pd.DataFrame(workloads)

            fig_workload = px.bar(
                w_df,
                x="employee_name",
                y=["open_tasks", "done_tasks", "blocked_tasks"],
                title="Task Distribution by Employee",
                labels={"value": "Task Count", "employee_name": "Team Member", "variable": "Task Category"},
                color_discrete_map={"open_tasks": "#3b82f6", "done_tasks": "#10b981", "blocked_tasks": "#ef4444"},
                barmode="stack",
            )
            fig_workload.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_workload, use_container_width=True)

            st.markdown("#### Team Capacity Table")
            w_disp = w_df[["employee_name", "role", "department", "open_tasks", "done_tasks", "blocked_tasks", "open_hours", "total_hours"]]
            w_disp.columns = ["Employee", "Role", "Department", "Open Tasks", "Completed", "Blocked", "Open Hours", "Total Est. Hours"]
            st.dataframe(w_disp, use_container_width=True, hide_index=True)
        else:
            st.info("No workload distribution records available.")

    # -------------------------------------------------------------
    # TAB 4: NEW PROJECT & TASK CREATION
    # -------------------------------------------------------------
    with tab_new_proj:
        col_new_p, col_new_t = st.columns([1, 1])

        with col_new_p:
            st.subheader("📁 Create New Project")
            with st.form("create_project_form"):
                p_name = st.text_input("Project Name *", placeholder="e.g. NextGen Microservices")
                p_code = st.text_input("Project Code *", placeholder="e.g. PRJ-NGM")
                p_desc = st.text_area("Description", placeholder="Objectives and architecture deliverables...")
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    p_status = st.selectbox("Status", ["Planning", "In Progress", "Completed", "On Hold"], index=0)
                    p_start = st.date_input("Start Date", value=date.today())
                with col_c2:
                    p_prio = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=2)
                    p_target = st.date_input("Target Date", value=date.today() + timedelta(days=90))

                p_lead = st.selectbox(
                    "Project Lead",
                    options=[None] + list(emp_map.keys()),
                    format_func=lambda x: "Unassigned" if x is None else emp_map[x],
                )
                p_budget = st.number_input(f"Project Budget ({CURRENCY_SYMBOL})", min_value=0.0, value=50000.0, step=5000.0)

                submit_proj = st.form_submit_button("🚀 Create Project", type="primary", use_container_width=True)

                if submit_proj:
                    success, msg, pid = create_project(
                        name=p_name,
                        code=p_code,
                        description=p_desc,
                        status=p_status,
                        priority=p_prio,
                        lead_id=p_lead,
                        start_date=p_start,
                        target_date=p_target,
                        budget=p_budget,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        with col_new_t:
            st.subheader("📋 Create Task / Milestone")
            with st.form("create_task_form"):
                if not projects:
                    st.warning("Please create a project first before creating tasks.")
                else:
                    t_project_id = st.selectbox(
                        "Parent Project *",
                        options=list(proj_map.keys()),
                        format_func=lambda x: proj_map[x],
                    )
                    t_title = st.text_input("Task Title *", placeholder="e.g. Write integration test suite")
                    t_desc = st.text_area("Task Description", placeholder="Acceptance criteria and technical details...")
                    t_milestone = st.text_input("Milestone Name", placeholder="e.g. Phase 2: Testing")
                    
                    t_c1, t_c2 = st.columns(2)
                    with t_c1:
                        t_assignee = st.selectbox(
                            "Assigned To",
                            options=[None] + list(emp_map.keys()),
                            format_func=lambda x: "Unassigned" if x is None else emp_map[x],
                        )
                        t_status = st.selectbox("Initial Status", ["To Do", "In Progress", "Blocked", "Done"])
                    with t_c2:
                        t_priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"], index=2)
                        t_hours = st.number_input("Estimated Hours", min_value=1.0, value=8.0, step=2.0)

                    t_due = st.date_input("Due Date", value=date.today() + timedelta(days=14))

                    submit_task = st.form_submit_button("➕ Create Task", type="primary", use_container_width=True)

                    if submit_task:
                        success, msg, tid = create_task(
                            project_id=t_project_id,
                            title=t_title,
                            description=t_desc,
                            status=t_status,
                            priority=t_priority,
                            assigned_to_id=t_assignee,
                            milestone_name=t_milestone,
                            estimated_hours=t_hours,
                            due_date=t_due,
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
