"""
WorkSphere HR - Payroll & Compensation View
Salary structure maintenance, automated net pay calculations, pay-cycle history,
privacy masking toggle, and CSV payroll exports.
"""

import streamlit as st
import pandas as pd
from datetime import date
from services.payroll_service import (
    get_payroll_records,
    get_available_pay_periods,
    get_payroll_kpis,
    process_pay_run,
    export_payroll_to_csv,
    get_employee_salary_structure,
    update_salary_structure,
    calculate_net_pay,
)
from services.employee_service import get_all_employees, get_all_departments
from utils.ui_helpers import render_kpi_card, mask_currency, format_currency
from config import CURRENCY_SYMBOL


def render_payroll_view():
    st.title("💳 Payroll & Compensation Hub")
    st.caption("Administer compensation structures, process monthly pay cycles, mask confidential figures, and export audit sheets.")

    # 1. Top Bar: Privacy Mode Toggle & Pay Run Action
    top_col1, top_col2, top_col3 = st.columns([2.5, 1.5, 1.5])

    # Ensure privacy state is synced
    if "privacy_masked" not in st.session_state:
        st.session_state.privacy_masked = False

    with top_col1:
        # Prominent privacy toggle
        mask_toggle = st.toggle(
            "🔒 Mask Confidential Figures (Privacy Mode)",
            value=st.session_state.privacy_masked,
            help="When activated, replaces all sensitive salary, bonus, deduction, and net pay figures with masked bullets.",
            key="payroll_privacy_switch",
        )
        if mask_toggle != st.session_state.privacy_masked:
            st.session_state.privacy_masked = mask_toggle
            st.rerun()

    is_masked = st.session_state.privacy_masked

    # 2. Tabs
    tab_cycles, tab_run, tab_structures = st.tabs([
        "📜 Pay Cycle History & Records",
        "⚙️ Execute Monthly Pay Run",
        "💼 Employee Compensation Structures",
    ])

    employees = get_all_employees(active_only=True)
    emp_map = {e["id"]: f"{e['full_name']} ({e['emp_code']})" for e in employees}
    pay_periods = get_available_pay_periods()
    departments = get_all_departments()

    # -------------------------------------------------------------
    # TAB 1: PAY CYCLE HISTORY & AUDIT
    # -------------------------------------------------------------
    with tab_cycles:
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            sel_period = st.selectbox(
                "Select Pay Period",
                ["All Periods"] + pay_periods if pay_periods else ["No pay runs yet"],
                index=1 if len(pay_periods) > 0 else 0,
                key="payroll_sel_period",
            )
            period_query = sel_period if sel_period != "All Periods" and sel_period != "No pay runs yet" else None

        with filter_col2:
            sel_dept = st.selectbox(
                "Filter by Department",
                ["All Departments"] + [d["name"] for d in departments],
                key="payroll_dept_filter",
            )
            dept_id = next((d["id"] for d in departments if d["name"] == sel_dept), None) if sel_dept != "All Departments" else None

        with filter_col3:
            st.write("")
            st.write("")
            csv_data = export_payroll_to_csv(pay_period=period_query)
            st.download_button(
                label="📥 Export to CSV",
                data=csv_data,
                file_name=f"payroll_{sel_period or 'all'}.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=not bool(csv_data),
            )

        # KPI Summary row for selected period
        kpis = get_payroll_kpis(pay_period=period_query)
        kc1, kc2, kc3, kc4 = st.columns(4)
        with kc1:
            render_kpi_card("Total Gross Payroll", mask_currency(kpis["total_gross"], is_masked), "Gross compensation", "💰")
        with kc2:
            render_kpi_card("Total Net Disbursed", mask_currency(kpis["total_net"], is_masked), "Deposited to staff", "🏦")
        with kc3:
            render_kpi_card("PF Deductions Withheld", mask_currency(kpis["total_pf"], is_masked), "Retirement reserve", "🛡️")
        with kc4:
            render_kpi_card("Tax Withholdings", mask_currency(kpis["total_tax"], is_masked), "Income tax withheld", "🏛️")

        st.markdown("---")

        records = get_payroll_records(pay_period=period_query, department_id=dept_id)
        if records:
            display_recs = []
            for r in records:
                display_recs.append({
                    "Period": r["pay_period"],
                    "Emp Code": r["emp_code"],
                    "Employee": r["employee_name"],
                    "Department": r["department"],
                    "Base Salary": mask_currency(r["base_salary"], is_masked),
                    "Allowances": mask_currency(r["total_allowances"], is_masked),
                    "Bonus": mask_currency(r["bonuses"], is_masked),
                    "Gross Pay": mask_currency(r["gross_pay"], is_masked),
                    "PF Ded": mask_currency(r["pf_deduction"], is_masked),
                    "Tax Ded": mask_currency(r["tax_deduction"], is_masked),
                    "Total Ded": mask_currency(r["total_deductions"], is_masked),
                    "Net Pay": mask_currency(r["net_pay"], is_masked),
                    "Status": r["status"],
                    "Paid Date": str(r["payment_date"]),
                })
            st.dataframe(pd.DataFrame(display_recs), use_container_width=True, hide_index=True)
        else:
            st.info("No payroll records match the selected period and department filters.")

    # -------------------------------------------------------------
    # TAB 2: EXECUTE MONTHLY PAY RUN
    # -------------------------------------------------------------
    with tab_run:
        st.subheader("⚙️ Process Monthly Payroll Run")
        st.caption("Calculate gross wages, allowances, PF, and tax withholdings across all active staff.")

        with st.form("process_payroll_form"):
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                period_input = st.text_input("Pay Period (YYYY-MM) *", value=date.today().strftime("%Y-%m"), placeholder="e.g. 2026-11")
            with col_p2:
                payment_date = st.date_input("Disbursement / Value Date *", value=date.today())
            with col_p3:
                notes = st.text_input("Run Remarks", value="Standard monthly payroll run")

            confirm_check = st.checkbox("I verify that all attendance logs and leave approvals for this period have been finalized.")
            run_btn = st.form_submit_button("🚀 Run Company Payroll", type="primary", use_container_width=True)

            if run_btn:
                if not confirm_check:
                    st.error("Please confirm attendance and leave finalization before proceeding.")
                else:
                    success, msg, count = process_pay_run(
                        pay_period=period_input.strip(),
                        payment_date=payment_date,
                        notes=notes,
                    )
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # -------------------------------------------------------------
    # TAB 3: SALARY STRUCTURE EDITOR
    # -------------------------------------------------------------
    with tab_structures:
        st.subheader("💼 Compensation & Benefit Profiles")
        st.caption("Inspect and update individual employee salary baselines, allowances, and statutory deduction rates.")

        sel_sal_emp = st.selectbox(
            "Select Employee",
            options=list(emp_map.keys()),
            format_func=lambda x: emp_map[x],
            key="sal_struct_emp_sel",
        )

        if sel_sal_emp:
            curr_struct = get_employee_salary_structure(sel_sal_emp)
            if curr_struct:
                with st.form(f"sal_struct_form_{sel_sal_emp}"):
                    st.markdown("#### Earnings Breakdown")
                    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                    with c_s1:
                        base = st.number_input("Base Monthly Salary *", min_value=0.0, value=float(curr_struct["base_salary"]), step=250.0)
                    with c_s2:
                        housing = st.number_input("Housing Allowance", min_value=0.0, value=float(curr_struct["housing_allowance"]), step=100.0)
                    with c_s3:
                        transport = st.number_input("Transport Allowance", min_value=0.0, value=float(curr_struct["transport_allowance"]), step=50.0)
                    with c_s4:
                        other = st.number_input("Other Allowances", min_value=0.0, value=float(curr_struct["other_allowances"]), step=50.0)

                    st.markdown("#### Deductions & Statutory Rates")
                    c_d1, c_d2, c_d3 = st.columns(3)
                    with c_d1:
                        pf_pct = st.number_input("Provident Fund Rate (%)", min_value=0.0, max_value=0.5, value=float(curr_struct["pf_rate"]), step=0.01)
                    with c_d2:
                        tax_pct = st.number_input("Income Tax Withholding Rate (%)", min_value=0.0, max_value=0.5, value=float(curr_struct["tax_rate"]), step=0.01)
                    with c_d3:
                        std_ded = st.number_input("Standard Deductions", min_value=0.0, value=float(curr_struct["standard_deductions"]), step=25.0)

                    # Live preview calculation
                    preview = calculate_net_pay(
                        base_salary=base,
                        housing_allowance=housing,
                        transport_allowance=transport,
                        other_allowances=other,
                        bonus=0.0,
                        pf_rate=pf_pct,
                        tax_rate=tax_pct,
                        standard_deductions=std_ded,
                    )

                    st.info(
                        f"📊 **Calculated Monthly Net Pay**: {mask_currency(preview['net_pay'], is_masked)} "
                        f"(Gross: {mask_currency(preview['gross_pay'], is_masked)} | Total Deductions: {mask_currency(preview['total_deductions'], is_masked)})"
                    )

                    save_sal_btn = st.form_submit_button("💾 Update Compensation Structure", type="primary")

                    if save_sal_btn:
                        success, msg = update_salary_structure(
                            employee_id=sel_sal_emp,
                            base_salary=base,
                            housing=housing,
                            transport=transport,
                            other=other,
                            pf_rate=pf_pct,
                            tax_rate=tax_pct,
                            standard_deductions=std_ded,
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
