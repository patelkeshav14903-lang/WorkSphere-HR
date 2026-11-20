"""
WorkSphere HR - Payroll & Compensation Service
Business logic for base salary, allowances, bonuses, deductions, net pay calculation,
pay-cycle processing, and CSV export.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import joinedload
from db.connection import get_db
from db.models import SalaryStructure, PayrollRecord, Employee, Department
from config import CURRENCY_SYMBOL


def calculate_net_pay(
    base_salary: float,
    housing_allowance: float = 0.0,
    transport_allowance: float = 0.0,
    other_allowances: float = 0.0,
    bonus: float = 0.0,
    pf_rate: float = 0.05,
    tax_rate: float = 0.10,
    standard_deductions: float = 150.0,
) -> Dict[str, float]:
    """
    Standard net pay calculation engine.
    Formula:
      Total Allowances = Housing + Transport + Other
      Gross Pay = Base + Total Allowances + Bonus
      PF Deduction = Base * PF Rate
      Tax Deduction = Gross Pay * Tax Rate
      Total Deductions = PF + Tax + Standard Deductions
      Net Pay = Gross Pay - Total Deductions
    """
    total_allowances = round(housing_allowance + transport_allowance + other_allowances, 2)
    gross_pay = round(base_salary + total_allowances + bonus, 2)
    pf_deduction = round(base_salary * pf_rate, 2)
    tax_deduction = round(gross_pay * tax_rate, 2)
    total_deductions = round(pf_deduction + tax_deduction + standard_deductions, 2)
    net_pay = round(gross_pay - total_deductions, 2)

    return {
        "base_salary": base_salary,
        "housing_allowance": housing_allowance,
        "transport_allowance": transport_allowance,
        "other_allowances": other_allowances,
        "total_allowances": total_allowances,
        "bonus": bonus,
        "gross_pay": gross_pay,
        "pf_deduction": pf_deduction,
        "tax_deduction": tax_deduction,
        "standard_deductions": standard_deductions,
        "total_deductions": total_deductions,
        "net_pay": net_pay,
    }


def get_employee_salary_structure(employee_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve an employee's compensation breakdown."""
    with get_db() as db:
        sal = db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id).first()
        if not sal:
            return None
        return {
            "id": sal.id,
            "employee_id": sal.employee_id,
            "base_salary": sal.base_salary,
            "housing_allowance": sal.housing_allowance,
            "transport_allowance": sal.transport_allowance,
            "other_allowances": sal.other_allowances,
            "total_allowances": sal.total_allowances,
            "gross_monthly": sal.gross_monthly,
            "pf_rate": sal.pf_rate,
            "tax_rate": sal.tax_rate,
            "standard_deductions": sal.standard_deductions,
            "effective_date": sal.effective_date,
        }


def update_salary_structure(
    employee_id: int,
    base_salary: float,
    housing: float,
    transport: float,
    other: float,
    pf_rate: float,
    tax_rate: float,
    standard_deductions: float,
) -> Tuple[bool, str]:
    """Update or create an employee's salary structure."""
    if base_salary < 0 or housing < 0 or transport < 0 or other < 0:
        return False, "Salary amounts cannot be negative."

    with get_db() as db:
        sal = db.query(SalaryStructure).filter(SalaryStructure.employee_id == employee_id).first()
        if not sal:
            sal = SalaryStructure(employee_id=employee_id)
            db.add(sal)

        sal.base_salary = base_salary
        sal.housing_allowance = housing
        sal.transport_allowance = transport
        sal.other_allowances = other
        sal.pf_rate = pf_rate
        sal.tax_rate = tax_rate
        sal.standard_deductions = standard_deductions
        sal.effective_date = date.today()

    return True, "Salary structure updated successfully."


def process_pay_run(
    pay_period: str,
    payment_date: date,
    notes: Optional[str] = None,
) -> Tuple[bool, str, int]:
    """
    Execute a monthly payroll cycle for all active employees.
    Creates or updates PayrollRecords for the given pay_period (e.g. '2026-11').
    """
    with get_db() as db:
        employees = (
            db.query(Employee)
            .options(joinedload(Employee.salary_structure))
            .filter(Employee.is_active == True)
            .all()
        )

        if not employees:
            return False, "No active employees found to process payroll.", 0

        processed_count = 0
        for emp in employees:
            sal = emp.salary_structure
            if not sal:
                # Default baseline
                sal = SalaryStructure(
                    employee_id=emp.id,
                    base_salary=5000.0,
                    housing_allowance=750.0,
                    transport_allowance=250.0,
                    other_allowances=100.0,
                    pf_rate=0.05,
                    tax_rate=0.10,
                    standard_deductions=150.0,
                )
                db.add(sal)
                db.flush()

            calc = calculate_net_pay(
                base_salary=sal.base_salary,
                housing_allowance=sal.housing_allowance,
                transport_allowance=sal.transport_allowance,
                other_allowances=sal.other_allowances,
                bonus=0.0,
                pf_rate=sal.pf_rate,
                tax_rate=sal.tax_rate,
                standard_deductions=sal.standard_deductions,
            )

            # Check if record already exists for this pay_period and employee
            record = (
                db.query(PayrollRecord)
                .filter(
                    PayrollRecord.employee_id == emp.id,
                    PayrollRecord.pay_period == pay_period,
                )
                .first()
            )

            if record:
                record.payment_date = payment_date
                record.base_salary = calc["base_salary"]
                record.total_allowances = calc["total_allowances"]
                record.gross_pay = calc["gross_pay"]
                record.pf_deduction = calc["pf_deduction"]
                record.tax_deduction = calc["tax_deduction"]
                record.other_deductions = calc["standard_deductions"]
                record.total_deductions = calc["total_deductions"]
                record.net_pay = calc["net_pay"]
                record.status = "Paid"
                record.notes = notes or f"Pay cycle run {pay_period}"
            else:
                record = PayrollRecord(
                    employee_id=emp.id,
                    pay_period=pay_period,
                    payment_date=payment_date,
                    base_salary=calc["base_salary"],
                    total_allowances=calc["total_allowances"],
                    bonuses=0.0,
                    gross_pay=calc["gross_pay"],
                    pf_deduction=calc["pf_deduction"],
                    tax_deduction=calc["tax_deduction"],
                    other_deductions=calc["standard_deductions"],
                    total_deductions=calc["total_deductions"],
                    net_pay=calc["net_pay"],
                    status="Paid",
                    payment_method="Direct Deposit",
                    notes=notes or f"Pay cycle run {pay_period}",
                )
                db.add(record)

            processed_count += 1

    return True, f"Successfully processed payroll for {processed_count} employees for {pay_period}.", processed_count


def get_available_pay_periods() -> List[str]:
    """Retrieve list of distinct pay periods in descending order."""
    with get_db() as db:
        periods = (
            db.query(PayrollRecord.pay_period)
            .distinct()
            .order_by(PayrollRecord.pay_period.desc())
            .all()
        )
        return [p[0] for p in periods]


def get_payroll_records(
    pay_period: Optional[str] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Query payroll records with filters."""
    with get_db() as db:
        query = (
            db.query(PayrollRecord)
            .options(
                joinedload(PayrollRecord.employee).joinedload(Employee.department)
            )
        )

        if pay_period and pay_period != "All":
            query = query.filter(PayrollRecord.pay_period == pay_period)

        if employee_id:
            query = query.filter(PayrollRecord.employee_id == employee_id)

        if department_id:
            query = query.join(PayrollRecord.employee).filter(Employee.department_id == department_id)

        records = query.order_by(PayrollRecord.pay_period.desc(), PayrollRecord.id.desc()).all()

        results = []
        for r in records:
            results.append({
                "id": r.id,
                "pay_period": r.pay_period,
                "payment_date": r.payment_date,
                "employee_id": r.employee_id,
                "emp_code": r.employee.emp_code if r.employee else "N/A",
                "employee_name": r.employee.full_name if r.employee else "Unknown",
                "department": r.employee.department.name if r.employee and r.employee.department else "N/A",
                "role": r.employee.role if r.employee else "N/A",
                "base_salary": r.base_salary,
                "total_allowances": r.total_allowances,
                "bonuses": r.bonuses,
                "gross_pay": r.gross_pay,
                "pf_deduction": r.pf_deduction,
                "tax_deduction": r.tax_deduction,
                "other_deductions": r.other_deductions,
                "total_deductions": r.total_deductions,
                "net_pay": r.net_pay,
                "status": r.status,
                "payment_method": r.payment_method,
                "notes": r.notes or "",
            })
        return results


def export_payroll_to_csv(pay_period: Optional[str] = None) -> str:
    """Generate CSV string of payroll records for export."""
    records = get_payroll_records(pay_period=pay_period)
    if not records:
        return ""
    df = pd.DataFrame(records)
    return df.to_csv(index=False)


def get_payroll_kpis(pay_period: Optional[str] = None) -> Dict[str, Any]:
    """Calculate payroll aggregate figures."""
    records = get_payroll_records(pay_period=pay_period)
    if not records:
        return {
            "total_gross": 0.0,
            "total_net": 0.0,
            "total_deductions": 0.0,
            "total_pf": 0.0,
            "total_tax": 0.0,
            "employees_count": 0,
            "avg_net": 0.0,
        }

    total_gross = sum(r["gross_pay"] for r in records)
    total_net = sum(r["net_pay"] for r in records)
    total_ded = sum(r["total_deductions"] for r in records)
    total_pf = sum(r["pf_deduction"] for r in records)
    total_tax = sum(r["tax_deduction"] for r in records)
    count = len(records)

    return {
        "total_gross": round(total_gross, 2),
        "total_net": round(total_net, 2),
        "total_deductions": round(total_ded, 2),
        "total_pf": round(total_pf, 2),
        "total_tax": round(total_tax, 2),
        "employees_count": count,
        "avg_net": round(total_net / count, 2) if count > 0 else 0.0,
    }
