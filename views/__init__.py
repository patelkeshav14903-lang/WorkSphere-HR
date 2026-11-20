"""Views package initialization."""
from views.dashboard_view import render_dashboard_view
from views.employees_view import render_employees_view
from views.attendance_view import render_attendance_view
from views.leave_view import render_leave_view
from views.payroll_view import render_payroll_view
from views.projects_view import render_projects_view

__all__ = [
    "render_dashboard_view",
    "render_employees_view",
    "render_attendance_view",
    "render_leave_view",
    "render_payroll_view",
    "render_projects_view",
]
