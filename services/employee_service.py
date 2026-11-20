"""
WorkSphere HR - Employee Management Service
Business logic for employee records, directory querying, validation, and onboarding.
"""

from datetime import date, datetime
import re
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import joinedload
from db.connection import get_db
from db.models import Employee, Department, LeaveBalance, SalaryStructure
from config import LEAVE_DEFAULTS, DEFAULT_PF_RATE, DEFAULT_TAX_RATE, DEFAULT_STANDARD_DEDUCTION


def get_all_departments() -> List[Dict[str, Any]]:
    """Retrieve all departments."""
    with get_db() as db:
        depts = db.query(Department).order_by(Department.name.asc()).all()
        return [
            {"id": d.id, "name": d.name, "code": d.code, "description": d.description}
            for d in depts
        ]


def get_department_by_id(dept_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single department by ID."""
    with get_db() as db:
        d = db.query(Department).filter(Department.id == dept_id).first()
        if not d:
            return None
        return {"id": d.id, "name": d.name, "code": d.code, "description": d.description}


def get_all_employees(
    search_query: str = "",
    department_id: Optional[int] = None,
    onboarding_status: Optional[str] = None,
    employment_type: Optional[str] = None,
    active_only: bool = True,
) -> List[Dict[str, Any]]:
    """
    Search and filter employees with eager-loaded department and manager metadata.
    """
    with get_db() as db:
        query = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.manager),
                joinedload(Employee.salary_structure),
            )
        )

        if active_only:
            query = query.filter(Employee.is_active == True)

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if onboarding_status and onboarding_status != "All":
            query = query.filter(Employee.onboarding_status == onboarding_status)

        if employment_type and employment_type != "All":
            query = query.filter(Employee.employment_type == employment_type)

        employees = query.order_by(Employee.id.asc()).all()

        results = []
        for emp in employees:
            # In-memory search filter for combined multi-field match
            if search_query:
                q = search_query.lower()
                matches = (
                    q in emp.full_name.lower()
                    or q in emp.emp_code.lower()
                    or q in emp.email.lower()
                    or q in emp.role.lower()
                    or (emp.department and q in emp.department.name.lower())
                )
                if not matches:
                    continue

            results.append({
                "id": emp.id,
                "emp_code": emp.emp_code,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "full_name": emp.full_name,
                "email": emp.email,
                "phone": emp.phone or "N/A",
                "role": emp.role,
                "department_id": emp.department_id,
                "department_name": emp.department.name if emp.department else "Unassigned",
                "department_code": emp.department.code if emp.department else "N/A",
                "manager_id": emp.manager_id,
                "manager_name": emp.manager.full_name if emp.manager else "None (Executive)",
                "join_date": emp.join_date,
                "onboarding_status": emp.onboarding_status,
                "employment_type": emp.employment_type,
                "is_active": emp.is_active,
                "base_salary": emp.salary_structure.base_salary if emp.salary_structure else 0.0,
                "total_allowances": emp.salary_structure.total_allowances if emp.salary_structure else 0.0,
                "gross_monthly": emp.salary_structure.gross_monthly if emp.salary_structure else 0.0,
            })

        return results


def get_employee_by_id(emp_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full employee details by primary key."""
    with get_db() as db:
        emp = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.manager),
                joinedload(Employee.salary_structure),
            )
            .filter(Employee.id == emp_id)
            .first()
        )
        if not emp:
            return None

        # Direct reports
        direct_reports = (
            db.query(Employee)
            .filter(Employee.manager_id == emp.id, Employee.is_active == True)
            .all()
        )

        return {
            "id": emp.id,
            "emp_code": emp.emp_code,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "full_name": emp.full_name,
            "email": emp.email,
            "phone": emp.phone or "",
            "role": emp.role,
            "department_id": emp.department_id,
            "department_name": emp.department.name if emp.department else "Unassigned",
            "manager_id": emp.manager_id,
            "manager_name": emp.manager.full_name if emp.manager else "None (Executive)",
            "join_date": emp.join_date,
            "onboarding_status": emp.onboarding_status,
            "employment_type": emp.employment_type,
            "is_active": emp.is_active,
            "direct_reports": [r.full_name for r in direct_reports],
            "salary": {
                "base_salary": emp.salary_structure.base_salary if emp.salary_structure else 0.0,
                "housing_allowance": emp.salary_structure.housing_allowance if emp.salary_structure else 0.0,
                "transport_allowance": emp.salary_structure.transport_allowance if emp.salary_structure else 0.0,
                "other_allowances": emp.salary_structure.other_allowances if emp.salary_structure else 0.0,
                "pf_rate": emp.salary_structure.pf_rate if emp.salary_structure else DEFAULT_PF_RATE,
                "tax_rate": emp.salary_structure.tax_rate if emp.salary_structure else DEFAULT_TAX_RATE,
                "standard_deductions": emp.salary_structure.standard_deductions if emp.salary_structure else DEFAULT_STANDARD_DEDUCTION,
                "gross_monthly": emp.salary_structure.gross_monthly if emp.salary_structure else 0.0,
            } if emp.salary_structure else None,
        }


def get_employee_by_code(emp_code: str) -> Optional[Employee]:
    """Look up employee model by emp_code."""
    with get_db() as db:
        return db.query(Employee).filter(Employee.emp_code == emp_code).first()


def get_manager_candidates(exclude_emp_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """List employees eligible to be assigned as managers."""
    with get_db() as db:
        query = db.query(Employee).filter(Employee.is_active == True)
        if exclude_emp_id:
            query = query.filter(Employee.id != exclude_emp_id)
        candidates = query.order_by(Employee.first_name.asc()).all()
        return [{"id": c.id, "name": f"{c.full_name} ({c.role})"} for c in candidates]


def validate_employee_payload(
    payload: Dict[str, Any],
    is_update: bool = False,
    current_emp_id: Optional[int] = None,
) -> Tuple[bool, str]:
    """
    Validate employee data submission.
    Returns (True, "") if valid, or (False, "Error message") if invalid.
    """
    first_name = payload.get("first_name", "").strip()
    last_name = payload.get("last_name", "").strip()
    email = payload.get("email", "").strip().lower()
    emp_code = payload.get("emp_code", "").strip().upper()
    role = payload.get("role", "").strip()
    department_id = payload.get("department_id")

    if not first_name:
        return False, "First Name cannot be empty."
    if not last_name:
        return False, "Last Name cannot be empty."
    if not role:
        return False, "Job Role cannot be empty."
    if not department_id:
        return False, "Please select a valid Department."

    # Email format validation
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        return False, f"Invalid email format: '{email}'"

    # Emp code format check
    if not emp_code:
        return False, "Employee Code cannot be empty."

    with get_db() as db:
        # Check email uniqueness
        email_query = db.query(Employee).filter(Employee.email == email)
        if is_update and current_emp_id:
            email_query = email_query.filter(Employee.id != current_emp_id)
        if email_query.first():
            return False, f"Email '{email}' is already assigned to another employee."

        # Check emp_code uniqueness
        code_query = db.query(Employee).filter(Employee.emp_code == emp_code)
        if is_update and current_emp_id:
            code_query = code_query.filter(Employee.id != current_emp_id)
        if code_query.first():
            return False, f"Employee Code '{emp_code}' is already registered."

    # Validate salary fields if provided
    base_salary = payload.get("base_salary", 0.0)
    try:
        if float(base_salary) < 0:
            return False, "Base salary cannot be negative."
    except (ValueError, TypeError):
        return False, "Base salary must be a valid numeric amount."

    return True, ""


def create_employee(payload: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """
    Create a new employee and automatically configure their initial leave balances
    and salary structure.
    """
    is_valid, error = validate_employee_payload(payload, is_update=False)
    if not is_valid:
        return False, error, None

    with get_db() as db:
        new_emp = Employee(
            emp_code=payload["emp_code"].strip().upper(),
            first_name=payload["first_name"].strip(),
            last_name=payload["last_name"].strip(),
            email=payload["email"].strip().lower(),
            phone=payload.get("phone", "").strip(),
            role=payload["role"].strip(),
            department_id=int(payload["department_id"]),
            manager_id=int(payload["manager_id"]) if payload.get("manager_id") else None,
            join_date=payload.get("join_date", date.today()),
            onboarding_status=payload.get("onboarding_status", "Pending"),
            employment_type=payload.get("employment_type", "Full-Time"),
            is_active=True,
        )
        db.add(new_emp)
        db.flush()  # Populates new_emp.id

        # Initialize Leave Balances for current year
        leave_bal = LeaveBalance(
            employee_id=new_emp.id,
            year=datetime.utcnow().year,
            casual_total=LEAVE_DEFAULTS["casual_leave"],
            casual_used=0.0,
            sick_total=LEAVE_DEFAULTS["sick_leave"],
            sick_used=0.0,
            earned_total=LEAVE_DEFAULTS["earned_leave"],
            earned_used=0.0,
        )
        db.add(leave_bal)

        # Initialize Salary Structure
        base_salary = float(payload.get("base_salary", 5000.0))
        housing = float(payload.get("housing_allowance", round(base_salary * 0.15, 2)))
        transport = float(payload.get("transport_allowance", 300.0))
        other = float(payload.get("other_allowances", 150.0))
        pf_rate = float(payload.get("pf_rate", DEFAULT_PF_RATE))
        tax_rate = float(payload.get("tax_rate", DEFAULT_TAX_RATE))
        std_ded = float(payload.get("standard_deductions", DEFAULT_STANDARD_DEDUCTION))

        salary = SalaryStructure(
            employee_id=new_emp.id,
            base_salary=base_salary,
            housing_allowance=housing,
            transport_allowance=transport,
            other_allowances=other,
            pf_rate=pf_rate,
            tax_rate=tax_rate,
            standard_deductions=std_ded,
            effective_date=date.today(),
        )
        db.add(salary)
        emp_id = new_emp.id

    return True, f"Employee {payload['first_name']} {payload['last_name']} ({payload['emp_code']}) created successfully!", emp_id


def update_employee(emp_id: int, payload: Dict[str, Any]) -> Tuple[bool, str]:
    """Update existing employee details and salary structure."""
    is_valid, error = validate_employee_payload(payload, is_update=True, current_emp_id=emp_id)
    if not is_valid:
        return False, error

    with get_db() as db:
        emp = db.query(Employee).filter(Employee.id == emp_id).first()
        if not emp:
            return False, "Employee record not found."

        emp.first_name = payload["first_name"].strip()
        emp.last_name = payload["last_name"].strip()
        emp.email = payload["email"].strip().lower()
        emp.phone = payload.get("phone", "").strip()
        emp.role = payload["role"].strip()
        emp.department_id = int(payload["department_id"])
        emp.manager_id = int(payload["manager_id"]) if payload.get("manager_id") else None
        if "join_date" in payload and payload["join_date"]:
            emp.join_date = payload["join_date"]
        emp.onboarding_status = payload.get("onboarding_status", emp.onboarding_status)
        emp.employment_type = payload.get("employment_type", emp.employment_type)
        if "is_active" in payload:
            emp.is_active = bool(payload["is_active"])

        # Update salary structure if provided
        if "base_salary" in payload:
            sal = db.query(SalaryStructure).filter(SalaryStructure.employee_id == emp_id).first()
            if not sal:
                sal = SalaryStructure(employee_id=emp_id)
                db.add(sal)
            sal.base_salary = float(payload.get("base_salary", sal.base_salary))
            sal.housing_allowance = float(payload.get("housing_allowance", sal.housing_allowance))
            sal.transport_allowance = float(payload.get("transport_allowance", sal.transport_allowance))
            sal.other_allowances = float(payload.get("other_allowances", sal.other_allowances))
            sal.pf_rate = float(payload.get("pf_rate", sal.pf_rate))
            sal.tax_rate = float(payload.get("tax_rate", sal.tax_rate))
            sal.standard_deductions = float(payload.get("standard_deductions", sal.standard_deductions))

    return True, f"Employee {payload['first_name']} {payload['last_name']} updated successfully."


def toggle_employee_status(emp_id: int) -> Tuple[bool, str]:
    """Toggle employee active/inactive status."""
    with get_db() as db:
        emp = db.query(Employee).filter(Employee.id == emp_id).first()
        if not emp:
            return False, "Employee not found."
        emp.is_active = not emp.is_active
        new_status = "Active" if emp.is_active else "Inactive"
        return True, f"Employee status updated to {new_status}."


def get_employee_stats() -> Dict[str, Any]:
    """Calculate executive stats for employees."""
    with get_db() as db:
        total = db.query(Employee).count()
        active = db.query(Employee).filter(Employee.is_active == True).count()
        completed_onboarding = (
            db.query(Employee)
            .filter(Employee.onboarding_status == "Completed", Employee.is_active == True)
            .count()
        )
        in_progress_onboarding = (
            db.query(Employee)
            .filter(Employee.onboarding_status == "In Progress", Employee.is_active == True)
            .count()
        )
        pending_onboarding = (
            db.query(Employee)
            .filter(Employee.onboarding_status == "Pending", Employee.is_active == True)
            .count()
        )

        # Department distribution
        depts = db.query(Department).all()
        dept_dist = {}
        for d in depts:
            cnt = (
                db.query(Employee)
                .filter(Employee.department_id == d.id, Employee.is_active == True)
                .count()
            )
            dept_dist[d.name] = cnt

        return {
            "total_employees": total,
            "active_employees": active,
            "inactive_employees": total - active,
            "completed_onboarding": completed_onboarding,
            "in_progress_onboarding": in_progress_onboarding,
            "pending_onboarding": pending_onboarding,
            "department_distribution": dept_dist,
        }
