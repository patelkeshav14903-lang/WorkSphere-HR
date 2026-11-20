"""
WorkSphere HR - Leave Management Service
Business logic for leave balance tracking, request submissions, approval/rejection workflows,
and team calendar views.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import joinedload
from db.connection import get_db
from db.models import LeaveBalance, LeaveRequest, Employee, Department
from config import LEAVE_DEFAULTS


def _calculate_business_days(start_date: date, end_date: date) -> float:
    """Calculate the number of business days (Monday-Friday) between two dates inclusive."""
    if start_date > end_date:
        return 0.0

    days_count = 0
    cur = start_date
    while cur <= end_date:
        if cur.weekday() < 5:  # Monday to Friday
            days_count += 1
        cur += timedelta(days=1)
    return float(days_count)


def get_employee_leave_balance(employee_id: int, year: Optional[int] = None) -> Dict[str, Any]:
    """Retrieve an employee's leave balance breakdown for the given year."""
    target_year = year or datetime.utcnow().year
    with get_db() as db:
        bal = (
            db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == target_year)
            .first()
        )

        if not bal:
            # Auto-provision if missing
            bal = LeaveBalance(
                employee_id=employee_id,
                year=target_year,
                casual_total=LEAVE_DEFAULTS["casual_leave"],
                casual_used=0.0,
                sick_total=LEAVE_DEFAULTS["sick_leave"],
                sick_used=0.0,
                earned_total=LEAVE_DEFAULTS["earned_leave"],
                earned_used=0.0,
            )
            db.add(bal)
            db.flush()

        return {
            "year": bal.year,
            "casual": {
                "total": bal.casual_total,
                "used": bal.casual_used,
                "remaining": bal.casual_remaining,
            },
            "sick": {
                "total": bal.sick_total,
                "used": bal.sick_used,
                "remaining": bal.sick_remaining,
            },
            "earned": {
                "total": bal.earned_total,
                "used": bal.earned_used,
                "remaining": bal.earned_remaining,
            },
            "total_allowed": bal.casual_total + bal.sick_total + bal.earned_total,
            "total_used": bal.casual_used + bal.sick_used + bal.earned_used,
            "total_remaining": bal.casual_remaining + bal.sick_remaining + bal.earned_remaining,
        }


def get_all_leave_balances(year: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve leave balances for all active employees."""
    target_year = year or datetime.utcnow().year
    with get_db() as db:
        employees = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.leave_balances),
            )
            .filter(Employee.is_active == True)
            .order_by(Employee.first_name.asc())
            .all()
        )

        results = []
        for emp in employees:
            bal = next((b for b in emp.leave_balances if b.year == target_year), None)
            if not bal:
                bal = LeaveBalance(
                    employee_id=emp.id,
                    year=target_year,
                    casual_total=LEAVE_DEFAULTS["casual_leave"],
                    casual_used=0.0,
                    sick_total=LEAVE_DEFAULTS["sick_leave"],
                    sick_used=0.0,
                    earned_total=LEAVE_DEFAULTS["earned_leave"],
                    earned_used=0.0,
                )
                db.add(bal)
                db.flush()

            results.append({
                "employee_id": emp.id,
                "emp_code": emp.emp_code,
                "employee_name": emp.full_name,
                "department": emp.department.name if emp.department else "N/A",
                "casual_total": bal.casual_total,
                "casual_used": bal.casual_used,
                "casual_remaining": bal.casual_remaining,
                "sick_total": bal.sick_total,
                "sick_used": bal.sick_used,
                "sick_remaining": bal.sick_remaining,
                "earned_total": bal.earned_total,
                "earned_used": bal.earned_used,
                "earned_remaining": bal.earned_remaining,
                "total_remaining": bal.casual_remaining + bal.sick_remaining + bal.earned_remaining,
            })
        return results


def submit_leave_request(
    employee_id: int,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: str,
) -> Tuple[bool, str, Optional[int]]:
    """
    Validate and persist an employee's leave request.
    Verifies date sequence and available balance quota.
    """
    valid_types = ["Casual", "Sick", "Earned"]
    if leave_type not in valid_types:
        return False, f"Invalid leave type. Choose from {valid_types}.", None

    if start_date > end_date:
        return False, "Start date cannot be after end date.", None

    days_requested = _calculate_business_days(start_date, end_date)
    if days_requested <= 0:
        return False, "Leave duration must include at least 1 working day.", None

    if not reason.strip():
        return False, "Please provide a reason for the leave request.", None

    with get_db() as db:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return False, "Employee not found.", None

        # Check balance
        bal = (
            db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == start_date.year)
            .first()
        )
        if not bal:
            bal = LeaveBalance(employee_id=employee_id, year=start_date.year)
            db.add(bal)
            db.flush()

        remaining = 0.0
        if leave_type == "Casual":
            remaining = bal.casual_remaining
        elif leave_type == "Sick":
            remaining = bal.sick_remaining
        elif leave_type == "Earned":
            remaining = bal.earned_remaining

        if days_requested > remaining:
            return (
                False,
                f"Insufficient {leave_type} balance. Requested: {days_requested} days, Available: {remaining} days.",
                None,
            )

        new_req = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=reason.strip(),
            status="Pending",
            created_at=datetime.utcnow(),
        )
        db.add(new_req)
        db.flush()
        req_id = new_req.id

    return True, f"Leave request for {days_requested} day(s) submitted successfully.", req_id


def review_leave_request(
    request_id: int,
    reviewer_id: int,
    action: str,
    comments: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Approve or reject a leave request.
    If approved, deducts days from the employee's LeaveBalance.
    """
    if action not in ["Approved", "Rejected"]:
        return False, "Action must be 'Approved' or 'Rejected'."

    with get_db() as db:
        req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not req:
            return False, "Leave request not found."

        if req.status != "Pending":
            return False, f"Request is already '{req.status}' and cannot be reviewed again."

        req.status = action
        req.reviewed_by_id = reviewer_id
        req.review_notes = comments or ""
        req.reviewed_at = datetime.utcnow()

        # If approved, deduct from balance
        if action == "Approved":
            bal = (
                db.query(LeaveBalance)
                .filter(
                    LeaveBalance.employee_id == req.employee_id,
                    LeaveBalance.year == req.start_date.year,
                )
                .first()
            )
            if bal:
                if req.leave_type == "Casual":
                    bal.casual_used += req.days_requested
                elif req.leave_type == "Sick":
                    bal.sick_used += req.days_requested
                elif req.leave_type == "Earned":
                    bal.earned_used += req.days_requested

        action_word = "approved" if action == "Approved" else "rejected"
        return True, f"Leave request #{request_id} has been {action_word}."


def get_leave_requests(
    status_filter: Optional[str] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Query leave requests with optional filters."""
    with get_db() as db:
        query = (
            db.query(LeaveRequest)
            .options(
                joinedload(LeaveRequest.employee).joinedload(Employee.department),
                joinedload(LeaveRequest.reviewer),
            )
        )

        if status_filter and status_filter != "All":
            query = query.filter(LeaveRequest.status == status_filter)

        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)

        if department_id:
            query = query.join(LeaveRequest.employee).filter(Employee.department_id == department_id)

        requests = query.order_by(LeaveRequest.created_at.desc()).all()

        results = []
        for r in requests:
            results.append({
                "id": r.id,
                "employee_id": r.employee_id,
                "emp_code": r.employee.emp_code if r.employee else "N/A",
                "employee_name": r.employee.full_name if r.employee else "Unknown",
                "department": r.employee.department.name if r.employee and r.employee.department else "N/A",
                "leave_type": r.leave_type,
                "start_date": r.start_date,
                "end_date": r.end_date,
                "days_requested": r.days_requested,
                "reason": r.reason,
                "status": r.status,
                "reviewer_name": r.reviewer.full_name if r.reviewer else "--",
                "review_notes": r.review_notes or "",
                "created_at": r.created_at,
                "reviewed_at": r.reviewed_at,
            })
        return results


def get_team_leave_calendar(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """
    Retrieve overlapping leaves within a target window for team calendar / timeline view.
    """
    with get_db() as db:
        leaves = (
            db.query(LeaveRequest)
            .options(joinedload(LeaveRequest.employee).joinedload(Employee.department))
            .filter(
                LeaveRequest.status.in_(["Approved", "Pending"]),
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
            .order_by(LeaveRequest.start_date.asc())
            .all()
        )

        return [
            {
                "id": l.id,
                "employee_name": l.employee.full_name if l.employee else "Unknown",
                "emp_code": l.employee.emp_code if l.employee else "",
                "department": l.employee.department.name if l.employee and l.employee.department else "N/A",
                "leave_type": l.leave_type,
                "start_date": l.start_date,
                "end_date": l.end_date,
                "days": l.days_requested,
                "status": l.status,
                "reason": l.reason,
            }
            for l in leaves
        ]


def get_leave_kpis() -> Dict[str, Any]:
    """Calculate leave KPI summary metrics."""
    with get_db() as db:
        pending_cnt = db.query(LeaveRequest).filter(LeaveRequest.status == "Pending").count()
        approved_cnt = db.query(LeaveRequest).filter(LeaveRequest.status == "Approved").count()
        today = date.today()

        # Employees on leave today
        on_leave_today = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.status == "Approved",
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
            )
            .count()
        )

        return {
            "pending_count": pending_cnt,
            "approved_count": approved_cnt,
            "on_leave_today_count": on_leave_today,
        }
