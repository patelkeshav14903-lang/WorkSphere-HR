# 💼 WorkSphere HR & Project Management Hub

An enterprise-grade, modular, Streamlit-friendly Python application integrating human capital management (HRIS), automated attendance tracking, leave request approval workflows, payroll processing with privacy masking, and project deliverable tracking.

---

## 🌟 Key Features

### 👥 Employee Records
- **Searchable & Filterable Directory**: Filter by department, onboarding status (`Completed`, `In Progress`, `Pending`), and employment type (`Full-Time`, `Part-Time`, `Contract`).
- **Profile Drawers & Expanders**: Detailed view of corporate metadata, job role, reporting line / manager hierarchy, join date, direct reports, and compensation structures.
- **Form Validation & CRUD**: Add new employees and edit existing profiles with strict email format, employee code uniqueness, and salary numeric validation.

### ⏱️ Attendance & Time Tracking
- **Daily Check-In/Check-Out Logging**: Log and update attendance with automatic working hours computation.
- **Status Tracking**: Categorize workforce presence as `Present` (On-site), `Remote` (WFH), `Late`, `Absent`, or `On Leave`.
- **Live Attendance Roster**: Real-time snapshot of today's attendance rate and active headcounts.
- **Monthly Attendance Summaries**: Aggregates logged days, present counts, remote days, tardiness, total working hours, and overall attendance rate per staff member.

### 🏖️ Leave Management & Workflow
- **Category Quota Tracking**: Manages annual allowances for `Casual Leave`, `Sick Leave`, and `Earned/Annual Leave`.
- **Request Submission**: Business-day calculation engine, balance sufficiency validation, and date-range verification.
- **Approval / Rejection Workflow**: Dedicated manager/HR review interface with comment auditing; balance is automatically deducted upon approval.
- **Team Leave Schedule**: Date-window calendar view of all approved and pending absences across departments.

### 💳 Payroll & Compensation System
- **Comprehensive Structure**: Base salary, housing allowances, transport allowances, custom allowances, bonuses, and statutory deductions.
- **Automated Net Pay Engine**: Calculates Provident Fund (PF), withholding tax, and standard deductions against gross compensation.
- **🔒 Privacy Masking Mode**: One-click toggle in the sidebar and top toolbar to mask all sensitive salary, bonus, deduction, and net pay figures with bullets (`$ ••••••`).
- **Pay Run Execution**: Batch process monthly pay runs for all active staff (e.g. `2026-11`).
- **Audit History & CSV Export**: Instant one-click CSV export of finalized payroll statements.

### 🚀 Project & Workload Management
- **Project Portfolio**: Track project progress (%), priorities (`Critical`, `High`, `Medium`, `Low`), target deadlines, budget allocation, and assigned leads.
- **Tasks & Milestones Board**: Lifecycle task tracking (`To Do`, `In Progress`, `Blocked`, `Done`) with a quick status updater tool.
- **Assignee Links**: Directly connects project deliverables to employee profiles.
- **Workload & Capacity Analytics**: Interactive visual charts showing open vs. completed task distribution and total hours per team member to balance resource allocation.

---

## 🏗️ Architecture & Project Structure

The project strictly decouples data access (`db/`) and business logic (`services/`) from the presentation layer (`views/` and `app.py`):

```
WorkSphere HR/
├── app.py                     # Main Streamlit entrance, page switcher / router, layout
├── config.py                  # App configuration, DB URI, currency, constants
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation and setup guide
│
├── db/                        # Database Layer (Agnostic SQLite / PostgreSQL)
│   ├── __init__.py
│   ├── connection.py          # SQLAlchemy engine, sessionmaker, transaction context
│   ├── models.py              # Declarative SQLAlchemy models & relationships
│   └── seed.py                # Realistic seed-data generator script
│
├── services/                  # Pure Business Logic (No Streamlit dependencies)
│   ├── __init__.py
│   ├── employee_service.py    # Employee CRUD, directory filtering, input validation
│   ├── attendance_service.py  # Check-in/out, hours computation, monthly aggregates
│   ├── leave_service.py       # Quotas, request validation, approval workflow
│   ├── payroll_service.py     # Net pay calculations, pay-run processing, CSV export
│   └── project_service.py     # Projects, tasks, milestones, workload distribution
│
├── views/                     # Streamlit Presentation Views
│   ├── __init__.py
│   ├── dashboard_view.py      # Executive overview KPIs, Plotly charts, alerts
│   ├── employees_view.py      # Directory, profile cards/drawers, add/edit forms
│   ├── attendance_view.py     # Daily logger, live roster, history query, monthly summary
│   ├── leave_view.py          # Balance quotas, request form, review workflow, calendar
│   ├── payroll_view.py        # Compensation tables, privacy toggle, pay runs, CSV
│   └── projects_view.py       # Project portfolio, task lifecycle board, workload metrics
│
└── utils/                     # UI Formatting & Helpers
    ├── __init__.py
    └── ui_helpers.py          # Custom CSS, status badges, KPI cards, privacy masking
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```
> **Note**: On the first launch, the app automatically initializes `worksphere.db` SQLite database and populates it with realistic seed data (15 employees across 6 departments, attendance records, leave balances/requests, payroll history, and 5 active projects with deliverables).

---

## 🗄️ Database: Swapping to PostgreSQL

The application uses SQLAlchemy with unified schema models, making swapping to PostgreSQL effortless:

1. Install PostgreSQL driver:
   ```bash
   pip install psycopg2-binary
   ```
2. Set the `DATABASE_URL` environment variable:
   ```bash
   # Linux / macOS
   export DATABASE_URL="postgresql://username:password@localhost:5432/worksphere_hr"

   # Windows PowerShell
   $env:DATABASE_URL="postgresql://username:password@localhost:5432/worksphere_hr"
   ```
3. Run the application:
   ```bash
   streamlit run app.py
   ```
   The engine automatically detects the connection string, creates tables, and seeds the initial dataset.

---

## 🛠️ Testing & Verification

To verify that all database models, services, and calculations run without errors:
```bash
python -c "
import db.connection, db.models, db.seed
import services.employee_service as es
import services.attendance_service as ats
import services.leave_service as ls
import services.payroll_service as ps
import services.project_service as prjs

print('Employees:', len(es.get_all_employees()))
print('Attendance KPIs:', ats.get_attendance_kpis())
print('Leave KPIs:', ls.get_leave_kpis())
print('Payroll KPIs:', ps.get_payroll_kpis())
print('Project KPIs:', prjs.get_project_kpis())
print('All modules operational!')
"
```
