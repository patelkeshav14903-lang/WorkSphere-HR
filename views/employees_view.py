"""
WorkSphere HR - Employee Records & Directory View
Searchable/filterable directory, profile drawer/expander, onboarding tracking,
and validated record creation/editing.
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.employee_service import (
    get_all_employees,
    get_employee_by_id,
    get_all_departments,
    get_manager_candidates,
    create_employee,
    update_employee,
    toggle_employee_status,
)
from utils.ui_helpers import mask_currency, render_badge, format_currency
from config import CURRENCY_SYMBOL


def render_employees_view():
    st.title("👥 Employee Records & Directory")
    st.caption("Centralized human capital directory with role metadata, onboarding lifecycle, and profile management.")

    is_masked = st.session_state.get("privacy_masked", False)

    # Top action bar: Search & Filters
    col_search, col_dept, col_status, col_btn = st.columns([3, 2, 2, 1.8])

    with col_search:
        search_query = st.text_input(
            "🔍 Search Directory",
            placeholder="Search by name, EMP code, role, email...",
            key="emp_search_input",
        )

    # Department filter options
    departments = get_all_departments()
    dept_options = {d["id"]: d["name"] for d in departments}
    dept_choices = ["All Departments"] + [d["name"] for d in departments]

    with col_dept:
        selected_dept_name = st.selectbox("Department", dept_choices, key="emp_dept_filter")
        selected_dept_id = None
        if selected_dept_name != "All Departments":
            for d in departments:
                if d["name"] == selected_dept_name:
                    selected_dept_id = d["id"]
                    break

    with col_status:
        onboarding_filter = st.selectbox(
            "Onboarding Status",
            ["All", "Completed", "In Progress", "Pending"],
            key="emp_onboarding_filter",
        )

    with col_btn:
        st.write("")  # spacing
        st.write("")
        show_add_modal = st.button("➕ Add New Employee", type="primary", use_container_width=True)

    # State for add/edit toggle
    if "show_add_form" not in st.session_state:
        st.session_state.show_add_form = False
    if "editing_emp_id" not in st.session_state:
        st.session_state.editing_emp_id = None

    if show_add_modal:
        st.session_state.show_add_form = not st.session_state.show_add_form
        st.session_state.editing_emp_id = None

    # 1. ADD NEW EMPLOYEE FORM SECTION
    if st.session_state.show_add_form and st.session_state.editing_emp_id is None:
        with st.expander("📝 Register New Employee (Interactive Form)", expanded=True):
            st.subheader("New Employee Registration")
            st.caption("Enter employee corporate details, manager reporting line, and initial compensation.")

            with st.form("add_employee_form", clear_on_submit=False):
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    first_name = st.text_input("First Name *", placeholder="e.g. Jane")
                    email = st.text_input("Corporate Email *", placeholder="e.g. jane.doe@worksphere.io")
                    dept_id = st.selectbox(
                        "Department *",
                        options=list(dept_options.keys()),
                        format_func=lambda x: dept_options[x],
                    )
                    join_date = st.date_input("Joining Date *", value=date.today())

                with col_f2:
                    last_name = st.text_input("Last Name *", placeholder="e.g. Doe")
                    phone = st.text_input("Phone Number", placeholder="e.g. +1 (555) 000-0000")
                    manager_candidates = get_manager_candidates()
                    manager_options = [None] + [c["id"] for c in manager_candidates]
                    mgr_id = st.selectbox(
                        "Reporting Manager",
                        options=manager_options,
                        format_func=lambda x: next((c["name"] for c in manager_candidates if c["id"] == x), "None (Executive)"),
                    )
                    onboarding_status = st.selectbox(
                        "Onboarding Status",
                        options=["Pending", "In Progress", "Completed"],
                        index=0,
                    )

                with col_f3:
                    emp_code = st.text_input("Employee Code *", placeholder="e.g. EMP-1016")
                    role = st.text_input("Job Role / Title *", placeholder="e.g. Senior Backend Engineer")
                    emp_type = st.selectbox("Employment Type", ["Full-Time", "Part-Time", "Contract"])
                    base_salary = st.number_input(
                        f"Monthly Base Salary ({CURRENCY_SYMBOL}) *",
                        min_value=0.0,
                        value=6500.0,
                        step=500.0,
                    )

                submit_add = st.form_submit_button("✅ Create Employee Record", type="primary")

                if submit_add:
                    payload = {
                        "emp_code": emp_code,
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "phone": phone,
                        "role": role,
                        "department_id": dept_id,
                        "manager_id": mgr_id,
                        "join_date": join_date,
                        "onboarding_status": onboarding_status,
                        "employment_type": emp_type,
                        "base_salary": base_salary,
                    }
                    success, message, new_id = create_employee(payload)
                    if success:
                        st.success(message)
                        st.session_state.show_add_form = False
                        st.rerun()
                    else:
                        st.error(f"Validation Error: {message}")

    # 2. EDIT EMPLOYEE FORM SECTION
    if st.session_state.editing_emp_id:
        edit_emp = get_employee_by_id(st.session_state.editing_emp_id)
        if edit_emp:
            with st.expander(f"✏️ Editing Employee: {edit_emp['full_name']} ({edit_emp['emp_code']})", expanded=True):
                with st.form("edit_employee_form"):
                    col_e1, col_e2, col_e3 = st.columns(3)
                    with col_e1:
                        e_fname = st.text_input("First Name *", value=edit_emp["first_name"])
                        e_email = st.text_input("Corporate Email *", value=edit_emp["email"])
                        e_dept = st.selectbox(
                            "Department *",
                            options=list(dept_options.keys()),
                            index=list(dept_options.keys()).index(edit_emp["department_id"]) if edit_emp["department_id"] in dept_options else 0,
                            format_func=lambda x: dept_options[x],
                        )
                        e_join = st.date_input("Joining Date", value=edit_emp["join_date"])

                    with col_e2:
                        e_lname = st.text_input("Last Name *", value=edit_emp["last_name"])
                        e_phone = st.text_input("Phone Number", value=edit_emp["phone"])
                        mgr_candidates = get_manager_candidates(exclude_emp_id=edit_emp["id"])
                        mgr_opts = [None] + [c["id"] for c in mgr_candidates]
                        mgr_idx = mgr_opts.index(edit_emp["manager_id"]) if edit_emp["manager_id"] in mgr_opts else 0
                        e_mgr = st.selectbox(
                            "Reporting Manager",
                            options=mgr_opts,
                            index=mgr_idx,
                            format_func=lambda x: next((c["name"] for c in mgr_candidates if c["id"] == x), "None (Executive)"),
                        )
                        status_list = ["Pending", "In Progress", "Completed"]
                        e_onboard = st.selectbox(
                            "Onboarding Status",
                            options=status_list,
                            index=status_list.index(edit_emp["onboarding_status"]) if edit_emp["onboarding_status"] in status_list else 0,
                        )

                    with col_e3:
                        st.text_input("Employee Code (Locked)", value=edit_emp["emp_code"], disabled=True)
                        e_role = st.text_input("Job Role *", value=edit_emp["role"])
                        type_list = ["Full-Time", "Part-Time", "Contract"]
                        e_type = st.selectbox(
                            "Employment Type",
                            options=type_list,
                            index=type_list.index(edit_emp["employment_type"]) if edit_emp["employment_type"] in type_list else 0,
                        )
                        e_salary = st.number_input(
                            f"Monthly Base Salary ({CURRENCY_SYMBOL})",
                            min_value=0.0,
                            value=float(edit_emp["salary"]["base_salary"]) if edit_emp["salary"] else 5000.0,
                            step=500.0,
                        )

                    col_save, col_cancel = st.columns([1, 1])
                    with col_save:
                        submit_update = st.form_submit_button("💾 Save Changes", type="primary")
                    with col_cancel:
                        cancel_edit = st.form_submit_button("Cancel")

                    if cancel_edit:
                        st.session_state.editing_emp_id = None
                        st.rerun()

                    if submit_update:
                        payload = {
                            "first_name": e_fname,
                            "last_name": e_lname,
                            "email": e_email,
                            "phone": e_phone,
                            "role": e_role,
                            "department_id": e_dept,
                            "manager_id": e_mgr,
                            "join_date": e_join,
                            "onboarding_status": e_onboard,
                            "employment_type": e_type,
                            "base_salary": e_salary,
                        }
                        success, message = update_employee(edit_emp["id"], payload)
                        if success:
                            st.success(message)
                            st.session_state.editing_emp_id = None
                            st.rerun()
                        else:
                            st.error(message)

    # 3. DIRECTORY QUERY & DISPLAY
    employees = get_all_employees(
        search_query=search_query,
        department_id=selected_dept_id,
        onboarding_status=onboarding_filter,
    )

    st.markdown(f"**Found {len(employees)} employee record(s)**")

    # Display Directory in Tabbed Layout: Profile Cards & Tabular Table
    tab_cards, tab_table = st.tabs(["📇 Profile Cards & Drawers", "📋 Directory Table View"])

    with tab_cards:
        if not employees:
            st.info("No employee records match the given filter criteria.")
        else:
            # Render grid of employee cards
            for emp in employees:
                with st.expander(
                    f"**{emp['full_name']}** — {emp['role']} | {emp['department_name']} ({emp['emp_code']})",
                    expanded=False,
                ):
                    p_col1, p_col2, p_col3, p_col4 = st.columns([2.5, 2.5, 2.5, 1.5])

                    with p_col1:
                        st.markdown("**Personal & Corporate Metadata**")
                        st.markdown(f"• **Employee ID**: `{emp['emp_code']}`")
                        st.markdown(f"• **Email**: [{emp['email']}](mailto:{emp['email']})")
                        st.markdown(f"• **Phone**: `{emp['phone']}`")
                        st.markdown(f"• **Joined**: {emp['join_date'].strftime('%b %d, %Y')}")

                    with p_col2:
                        st.markdown("**Hierarchy & Status**")
                        st.markdown(f"• **Department**: {emp['department_name']}")
                        st.markdown(f"• **Manager**: {emp['manager_name']}")
                        st.markdown(f"• **Type**: {emp['employment_type']}")
                        st.markdown(
                            f"• **Onboarding**: {render_badge(emp['onboarding_status'], emp['onboarding_status'])}",
                            unsafe_allow_html=True,
                        )

                    with p_col3:
                        st.markdown("**Compensation & Total Pay**")
                        base_str = mask_currency(emp['base_salary'], is_masked=is_masked)
                        gross_str = mask_currency(emp['gross_monthly'], is_masked=is_masked)
                        st.markdown(f"• **Base Salary**: `{base_str}`")
                        st.markdown(f"• **Gross Monthly**: `{gross_str}`")
                        st.markdown(f"• **Account Status**: `{'Active' if emp['is_active'] else 'Inactive'}`")

                    with p_col4:
                        st.write("")
                        if st.button("✏️ Edit Profile", key=f"edit_btn_{emp['id']}", use_container_width=True):
                            st.session_state.editing_emp_id = emp["id"]
                            st.session_state.show_add_form = False
                            st.rerun()

                        toggle_label = "Deactivate" if emp["is_active"] else "Activate"
                        if st.button(toggle_label, key=f"toggle_btn_{emp['id']}", use_container_width=True):
                            toggle_employee_status(emp["id"])
                            st.rerun()

    with tab_table:
        if employees:
            table_records = []
            for e in employees:
                table_records.append({
                    "Code": e["emp_code"],
                    "Name": e["full_name"],
                    "Role": e["role"],
                    "Department": e["department_name"],
                    "Manager": e["manager_name"],
                    "Onboarding": e["onboarding_status"],
                    "Employment": e["employment_type"],
                    "Base Salary": mask_currency(e["base_salary"], is_masked=is_masked),
                    "Join Date": str(e["join_date"]),
                })
            df = pd.DataFrame(table_records)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No records to display.")
