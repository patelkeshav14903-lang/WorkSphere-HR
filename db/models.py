"""
WorkSphere HR - SQLAlchemy Data Models
Clean, relational schema portable across SQLite and PostgreSQL.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from db.connection import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    employees = relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department {self.code}: {self.name}>"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_code = Column(String(30), unique=True, nullable=False, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    role = Column(String(120), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    join_date = Column(Date, default=date.today, nullable=False)
    onboarding_status = Column(String(30), default="Pending", nullable=False)  # Pending, In Progress, Completed
    employment_type = Column(String(40), default="Full-Time", nullable=False)  # Full-Time, Part-Time, Contract
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    department = relationship("Department", back_populates="employees")
    manager = relationship("Employee", remote_side=[id], backref="direct_reports")
    attendance_records = relationship("AttendanceRecord", back_populates="employee", cascade="all, delete-orphan")
    leave_balances = relationship("LeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.employee_id", back_populates="employee", cascade="all, delete-orphan")
    salary_structure = relationship("SalaryStructure", back_populates="employee", uselist=False, cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")
    project_memberships = relationship("ProjectMember", back_populates="employee", cascade="all, delete-orphan")
    assigned_tasks = relationship("ProjectTask", back_populates="assignee")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee {self.emp_code}: {self.full_name}>"


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    check_in = Column(String(10), nullable=True)   # "09:15"
    check_out = Column(String(10), nullable=True)  # "18:05"
    status = Column(String(30), nullable=False)    # Present, Remote, Late, Absent, On Leave
    working_hours = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="attendance_records")

    def __repr__(self):
        return f"<Attendance emp={self.employee_id} date={self.date} status={self.status}>"


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, default=datetime.utcnow().year)
    casual_total = Column(Float, default=10.0)
    casual_used = Column(Float, default=0.0)
    sick_total = Column(Float, default=10.0)
    sick_used = Column(Float, default=0.0)
    earned_total = Column(Float, default=15.0)
    earned_used = Column(Float, default=0.0)

    employee = relationship("Employee", back_populates="leave_balances")

    @property
    def casual_remaining(self):
        return max(0.0, self.casual_total - self.casual_used)

    @property
    def sick_remaining(self):
        return max(0.0, self.sick_total - self.sick_used)

    @property
    def earned_remaining(self):
        return max(0.0, self.earned_total - self.earned_used)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    leave_type = Column(String(30), nullable=False)  # Casual, Sick, Earned
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(30), default="Pending", nullable=False)  # Pending, Approved, Rejected
    reviewed_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="leave_requests")
    reviewer = relationship("Employee", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<LeaveRequest emp={self.employee_id} type={self.leave_type} status={self.status}>"


class SalaryStructure(Base):
    __tablename__ = "salary_structures"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), unique=True, nullable=False)
    base_salary = Column(Float, nullable=False, default=0.0)
    housing_allowance = Column(Float, default=0.0)
    transport_allowance = Column(Float, default=0.0)
    other_allowances = Column(Float, default=0.0)
    pf_rate = Column(Float, default=0.05)           # 5% PF
    tax_rate = Column(Float, default=0.10)          # 10% Withholding Tax
    standard_deductions = Column(Float, default=150.0)
    effective_date = Column(Date, default=date.today)

    employee = relationship("Employee", back_populates="salary_structure")

    @property
    def total_allowances(self):
        return self.housing_allowance + self.transport_allowance + self.other_allowances

    @property
    def gross_monthly(self):
        return self.base_salary + self.total_allowances


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    pay_period = Column(String(20), nullable=False, index=True)  # YYYY-MM e.g. "2026-10"
    payment_date = Column(Date, nullable=False)
    base_salary = Column(Float, nullable=False)
    total_allowances = Column(Float, default=0.0)
    bonuses = Column(Float, default=0.0)
    gross_pay = Column(Float, nullable=False)
    pf_deduction = Column(Float, default=0.0)
    tax_deduction = Column(Float, default=0.0)
    other_deductions = Column(Float, default=0.0)
    total_deductions = Column(Float, nullable=False)
    net_pay = Column(Float, nullable=False)
    status = Column(String(30), default="Processed", nullable=False)  # Processed, Paid, Pending
    payment_method = Column(String(50), default="Direct Deposit")
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="payroll_records")

    def __repr__(self):
        return f"<Payroll emp={self.employee_id} period={self.pay_period} net={self.net_pay}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(30), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Planning", nullable=False)  # Planning, In Progress, Completed, On Hold
    priority = Column(String(30), default="Medium", nullable=False)  # Low, Medium, High, Critical
    lead_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    target_date = Column(Date, nullable=False)
    budget = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Employee", foreign_keys=[lead_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("ProjectTask", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.code}: {self.name}>"


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    role_in_project = Column(String(100), default="Contributor")

    project = relationship("Project", back_populates="members")
    employee = relationship("Employee", back_populates="project_memberships")


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="To Do", nullable=False)  # To Do, In Progress, Blocked, Done
    priority = Column(String(30), default="Medium", nullable=False)  # Low, Medium, High, Critical
    assigned_to_id = Column(Integer, ForeignKey("employees.id"), nullable=True, index=True)
    milestone_name = Column(String(120), nullable=True)
    estimated_hours = Column(Float, default=8.0)
    due_date = Column(Date, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Employee", back_populates="assigned_tasks")

    def __repr__(self):
        return f"<Task {self.title} status={self.status} assignee={self.assigned_to_id}>"
