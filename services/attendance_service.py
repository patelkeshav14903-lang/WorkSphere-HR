"""
WorkSphere HR - Attendance Service
Business logic for daily check-in/check-out logging, status tracking, and monthly summaries.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from db.connection import get_db
from db.models import AttendanceRecord, Employee, Department


def _calculate_hours(check_in_str: Optional[str], check_out_str: Optional[str]) -> float:
    """Calculate working hours between two 'HH:MM' strings."""
    if not check_in_str or not check_out_str:
        return 0.0
    try:
        t_in = datetime.strptime(check_in_str.strip(), "%H:%M")
        t_out = datetime.strptime(check_out_str.strip(), "%H:%M")
        diff_seconds = (t_out - t_in).total_seconds()
        if diff_seconds < 0:
            return 0.0
        return round(diff_seconds / 3600.0, 2)
    except Exception:
        return 0.0


def log_attendance(
    employee_id: int,
    log_date: date,
    check_in: Optional[str],
    check_out: Optional[str],
    status: str,
    notes: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Log or update a daily attendance record for an employee.
    Status choices: 'Present', 'Remote', 'Late', 'Absent', 'On Leave'.
    """
    valid_statuses = ["Present", "Remote", "Late", "Absent", "On Leave"]
    if status not in valid_statuses:
        return False, f"Invalid status '{status}'. Must be one of {valid_statuses}."

    calculated_hours = 0.0
    if status in ["Present", "Remote", "Late"]:
        calculated_hours = _calculate_hours(check_in, check_out)
        if not check_in and status != "Absent":
            # Default check-in time if omitted
            check_in = "09:00"

    with get_db() as db:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return False, f"Employee with ID {employee_id} does not exist."

        # Check if record already exists for this date and employee
        record = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.employee_id == employee_id, AttendanceRecord.date == log_date)
            .first()
        )

        if record:
            record.check_in = check_in
            record.check_out = check_out
            record.status = status
            record.working_hours = calculated_hours
            if notes is not None:
                record.notes = notes
            msg = f"Attendance updated for {emp.full_name} on {log_date}."
        else:
            record = AttendanceRecord(
                employee_id=employee_id,
                date=log_date,
                check_in=check_in,
                check_out=check_out,
                status=status,
                working_hours=calculated_hours,
                notes=notes or "Manual entry",
            )
            db.add(record)
            msg = f"Attendance logged for {emp.full_name} on {log_date} ({status})."

    return True, msg


def get_today_attendance(filter_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Retrieve all attendance entries for a given date (defaults to today)."""
    target_date = filter_date or date.today()
    with get_db() as db:
        records = (
            db.query(AttendanceRecord)
            .options(
                joinedload(AttendanceRecord.employee).joinedload(Employee.department)
            )
            .filter(AttendanceRecord.date == target_date)
            .order_by(AttendanceRecord.id.desc())
            .all()
        )

        results = []
        for r in records:
            results.append({
                "id": r.id,
                "employee_id": r.employee_id,
                "emp_code": r.employee.emp_code if r.employee else "N/A",
                "employee_name": r.employee.full_name if r.employee else "Unknown",
                "department": r.employee.department.name if r.employee and r.employee.department else "N/A",
                "date": r.date,
                "check_in": r.check_in or "--:--",
                "check_out": r.check_out or "--:--",
                "status": r.status,
                "working_hours": r.working_hours,
                "notes": r.notes or "",
            })
        return results


def get_attendance_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    status_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Query historical attendance records with flexible filtering."""
    with get_db() as db:
        query = (
            db.query(AttendanceRecord)
            .options(
                joinedload(AttendanceRecord.employee).joinedload(Employee.department)
            )
        )

        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)
        if employee_id:
            query = query.filter(AttendanceRecord.employee_id == employee_id)
        if status_filter and status_filter != "All":
            query = query.filter(AttendanceRecord.status == status_filter)

        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)

        records = query.order_by(AttendanceRecord.date.desc(), AttendanceRecord.id.desc()).all()

        return [
            {
                "id": r.id,
                "employee_id": r.employee_id,
                "emp_code": r.employee.emp_code if r.employee else "N/A",
                "employee_name": r.employee.full_name if r.employee else "Unknown",
                "department": r.employee.department.name if r.employee and r.employee.department else "N/A",
                "date": r.date,
                "check_in": r.check_in or "--:--",
                "check_out": r.check_out or "--:--",
                "status": r.status,
                "working_hours": r.working_hours,
                "notes": r.notes or "",
            }
            for r in records
        ]


def get_monthly_attendance_summary(year: int, month: int) -> List[Dict[str, Any]]:
    """
    Produce monthly aggregated attendance summary per employee:
    Present, Remote, Late, Absent, Total Hours, and Attendance Rate.
    """
    # Start and end date for the month
    start_dt = date(year, month, 1)
    if month == 12:
        end_dt = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_dt = date(year, month + 1, 1) - timedelta(days=1)

    with get_db() as db:
        employees = (
            db.query(Employee)
            .options(joinedload(Employee.department))
            .filter(Employee.is_active == True)
            .order_by(Employee.first_name.asc())
            .all()
        )

        summaries = []
        for emp in employees:
            recs = (
                db.query(AttendanceRecord)
                .filter(
                    AttendanceRecord.employee_id == emp.id,
                    AttendanceRecord.date >= start_dt,
                    AttendanceRecord.date <= end_dt,
                )
                .all()
            )

            total_days_logged = len(recs)
            present_cnt = sum(1 for r in recs if r.status == "Present")
            remote_cnt = sum(1 for r in recs if r.status == "Remote")
            late_cnt = sum(1 for r in recs if r.status == "Late")
            absent_cnt = sum(1 for r in recs if r.status == "Absent")
            leave_cnt = sum(1 for r in recs if r.status == "On Leave")
            total_hours = sum(r.working_hours for r in recs)

            # Attendance % based on recorded work days vs absences
            working_attendances = present_cnt + remote_cnt + late_cnt
            attend_rate = round((working_attendances / total_days_logged * 100), 1) if total_days_logged > 0 else 0.0

            summaries.append({
                "employee_id": emp.id,
                "emp_code": emp.emp_code,
                "employee_name": emp.full_name,
                "department": emp.department.name if emp.department else "N/A",
                "total_logged_days": total_days_logged,
                "present_days": present_cnt,
                "remote_days": remote_cnt,
                "late_days": late_cnt,
                "absent_days": absent_cnt,
                "on_leave_days": leave_cnt,
                "total_hours": round(total_hours, 1),
                "avg_hours_per_day": round(total_hours / working_attendances, 1) if working_attendances > 0 else 0.0,
                "attendance_rate": attend_rate,
            })

        return summaries


def get_attendance_kpis(target_date: Optional[date] = None) -> Dict[str, Any]:
    """Calculate key attendance metrics for dashboard overview."""
    check_date = target_date or date.today()
    with get_db() as db:
        total_active_employees = db.query(Employee).filter(Employee.is_active == True).count()
        today_records = (
            db.query(AttendanceRecord)
            .filter(AttendanceRecord.date == check_date)
            .all()
        )

        present = sum(1 for r in today_records if r.status == "Present")
        remote = sum(1 for r in today_records if r.status == "Remote")
        late = sum(1 for r in today_records if r.status == "Late")
        absent = sum(1 for r in today_records if r.status == "Absent")
        on_leave = sum(1 for r in today_records if r.status == "On Leave")

        total_working = present + remote + late
        logged_employees = len(today_records)
        unlogged = max(0, total_active_employees - logged_employees)

        attendance_rate = round((total_working / total_active_employees * 100), 1) if total_active_employees > 0 else 0.0

        return {
            "date": check_date,
            "total_active_employees": total_active_employees,
            "present_count": present,
            "remote_count": remote,
            "late_count": late,
            "absent_count": absent,
            "on_leave_count": on_leave,
            "not_logged_count": unlogged,
            "total_working": total_working,
            "attendance_rate": attendance_rate,
        }
