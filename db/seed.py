"""
WorkSphere HR - Comprehensive Seed Data Script
Populates a realistic corporate dataset across departments, employees,
attendance records, leave balances & requests, salary structures, payroll cycles,
and project management tasks.
"""

import sys
import os
from pathlib import Path

# Ensure root workspace directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from datetime import date, datetime, timedelta
import random
from db.connection import get_db, init_db
from db.models import (
    Department,
    Employee,
    AttendanceRecord,
    LeaveBalance,
    LeaveRequest,
    SalaryStructure,
    PayrollRecord,
    Project,
    ProjectMember,
    ProjectTask,
)


def seed_database(force_reseed: bool = False):
    """Seed the database if it is empty or force_reseed is True."""
    init_db()

    with get_db() as db:
        existing_emp_count = db.query(Employee).count()
        if existing_emp_count > 0 and not force_reseed:
            print(f"Database already populated ({existing_emp_count} employees found). Skipping seed.")
            return

        if force_reseed:
            print("Purging existing records for fresh reseed...")
            for table in [
                ProjectTask,
                ProjectMember,
                Project,
                PayrollRecord,
                SalaryStructure,
                LeaveRequest,
                LeaveBalance,
                AttendanceRecord,
                Employee,
                Department,
            ]:
                db.query(table).delete()
            db.flush()

        print("Seeding WorkSphere HR initial dataset...")

        # 1. Departments
        departments_data = [
            {"name": "Engineering", "code": "ENG", "description": "Core product engineering, infrastructure, and DevOps"},
            {"name": "Product & Design", "code": "PRD", "description": "Product management, UX/UI design, and user research"},
            {"name": "Human Resources", "code": "HR", "description": "Talent acquisition, culture, compensation, and people operations"},
            {"name": "Sales & Revenue", "code": "SLS", "description": "Enterprise sales, client solutions, and revenue operations"},
            {"name": "Finance & Legal", "code": "FIN", "description": "Financial planning, accounting, compliance, and governance"},
            {"name": "Marketing & Growth", "code": "MKT", "description": "Brand marketing, growth strategies, and communications"},
        ]
        dept_objs = {}
        for d in departments_data:
            dept = Department(**d)
            db.add(dept)
            dept_objs[d["code"]] = dept
        db.flush()

        # 2. Employees (Managers first, then reports)
        managers_data = [
            {
                "emp_code": "EMP-1001",
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "email": "sarah.jenkins@worksphere.io",
                "phone": "+1 (555) 234-5678",
                "role": "VP of Engineering",
                "department_id": dept_objs["ENG"].id,
                "manager_id": None,
                "join_date": date(2022, 3, 15),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1002",
                "first_name": "Alex",
                "last_name": "Chen",
                "email": "alex.chen@worksphere.io",
                "phone": "+1 (555) 345-6789",
                "role": "Head of Product",
                "department_id": dept_objs["PRD"].id,
                "manager_id": None,
                "join_date": date(2022, 6, 1),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1003",
                "first_name": "Rachel",
                "last_name": "Adams",
                "email": "rachel.adams@worksphere.io",
                "phone": "+1 (555) 456-7890",
                "role": "Director of People Ops",
                "department_id": dept_objs["HR"].id,
                "manager_id": None,
                "join_date": date(2022, 1, 10),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1004",
                "first_name": "Daniel",
                "last_name": "Torres",
                "email": "daniel.torres@worksphere.io",
                "phone": "+1 (555) 567-8901",
                "role": "VP of Sales & Revenue",
                "department_id": dept_objs["SLS"].id,
                "manager_id": None,
                "join_date": date(2023, 2, 20),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1005",
                "first_name": "Liam",
                "last_name": "O'Connor",
                "email": "liam.oconnor@worksphere.io",
                "phone": "+1 (555) 678-9012",
                "role": "Finance Controller",
                "department_id": dept_objs["FIN"].id,
                "manager_id": None,
                "join_date": date(2023, 4, 5),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
        ]

        emp_objs = {}
        for m in managers_data:
            emp = Employee(**m)
            db.add(emp)
            emp_objs[m["emp_code"]] = emp
        db.flush()

        # Staff employees reporting to managers
        staff_data = [
            {
                "emp_code": "EMP-1006",
                "first_name": "Marcus",
                "last_name": "Vance",
                "email": "marcus.vance@worksphere.io",
                "phone": "+1 (555) 789-0123",
                "role": "Lead Cloud Architect",
                "department_id": dept_objs["ENG"].id,
                "manager_id": emp_objs["EMP-1001"].id,
                "join_date": date(2023, 7, 1),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1007",
                "first_name": "Elena",
                "last_name": "Rostova",
                "email": "elena.rostova@worksphere.io",
                "phone": "+1 (555) 890-1234",
                "role": "Senior Full-Stack Engineer",
                "department_id": dept_objs["ENG"].id,
                "manager_id": emp_objs["EMP-1001"].id,
                "join_date": date(2023, 9, 15),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1008",
                "first_name": "David",
                "last_name": "Kim",
                "email": "david.kim@worksphere.io",
                "phone": "+1 (555) 901-2345",
                "role": "Frontend React Engineer",
                "department_id": dept_objs["ENG"].id,
                "manager_id": emp_objs["EMP-1001"].id,
                "join_date": date(2024, 2, 1),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1009",
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "priya.sharma@worksphere.io",
                "phone": "+1 (555) 012-3456",
                "role": "Site Reliability Engineer",
                "department_id": dept_objs["ENG"].id,
                "manager_id": emp_objs["EMP-1001"].id,
                "join_date": date(2024, 4, 10),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1010",
                "first_name": "Zoe",
                "last_name": "Martinez",
                "email": "zoe.martinez@worksphere.io",
                "phone": "+1 (555) 123-4560",
                "role": "Lead Product Designer",
                "department_id": dept_objs["PRD"].id,
                "manager_id": emp_objs["EMP-1002"].id,
                "join_date": date(2023, 11, 1),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1011",
                "first_name": "James",
                "last_name": "Wilson",
                "email": "james.wilson@worksphere.io",
                "phone": "+1 (555) 234-5671",
                "role": "Associate Product Manager",
                "department_id": dept_objs["PRD"].id,
                "manager_id": emp_objs["EMP-1002"].id,
                "join_date": date(2024, 8, 15),
                "onboarding_status": "In Progress",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1012",
                "first_name": "Samantha",
                "last_name": "Brooks",
                "email": "samantha.brooks@worksphere.io",
                "phone": "+1 (555) 345-6782",
                "role": "Talent Acquisition Specialist",
                "department_id": dept_objs["HR"].id,
                "manager_id": emp_objs["EMP-1003"].id,
                "join_date": date(2024, 1, 15),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1013",
                "first_name": "Kevin",
                "last_name": "Lee",
                "email": "kevin.lee@worksphere.io",
                "phone": "+1 (555) 456-7893",
                "role": "People Operations Coordinator",
                "department_id": dept_objs["HR"].id,
                "manager_id": emp_objs["EMP-1003"].id,
                "join_date": date(2024, 10, 1),
                "onboarding_status": "Pending",
                "employment_type": "Contract",
            },
            {
                "emp_code": "EMP-1014",
                "first_name": "Maya",
                "last_name": "Patel",
                "email": "maya.patel@worksphere.io",
                "phone": "+1 (555) 567-8904",
                "role": "Enterprise Account Executive",
                "department_id": dept_objs["SLS"].id,
                "manager_id": emp_objs["EMP-1004"].id,
                "join_date": date(2024, 3, 1),
                "onboarding_status": "Completed",
                "employment_type": "Full-Time",
            },
            {
                "emp_code": "EMP-1015",
                "first_name": "Lucas",
                "last_name": "Muller",
                "email": "lucas.muller@worksphere.io",
                "phone": "+1 (555) 678-9015",
                "role": "Growth Marketing Specialist",
                "department_id": dept_objs["MKT"].id,
                "manager_id": emp_objs["EMP-1004"].id,
                "join_date": date(2024, 5, 20),
                "onboarding_status": "In Progress",
                "employment_type": "Full-Time",
            },
        ]

        for s in staff_data:
            emp = Employee(**s)
            db.add(emp)
            emp_objs[s["emp_code"]] = emp
        db.flush()

        all_employees = list(emp_objs.values())

        # 3. Leave Balances for all employees
        for emp in all_employees:
            balance = LeaveBalance(
                employee_id=emp.id,
                year=2026,
                casual_total=10.0,
                casual_used=random.choice([0.0, 1.0, 2.0, 3.0]),
                sick_total=10.0,
                sick_used=random.choice([0.0, 1.0, 2.0]),
                earned_total=15.0,
                earned_used=random.choice([1.0, 3.0, 5.0, 7.0]),
            )
            db.add(balance)

        # 4. Leave Requests
        sample_requests = [
            {
                "employee_id": emp_objs["EMP-1007"].id,  # Elena
                "leave_type": "Casual",
                "start_date": date(2026, 11, 25),
                "end_date": date(2026, 11, 26),
                "days_requested": 2.0,
                "reason": "Family gathering and personal commitments",
                "status": "Approved",
                "reviewed_by_id": emp_objs["EMP-1001"].id,
                "review_notes": "Approved. Please ensure sprint items are handed off to David.",
                "reviewed_at": datetime(2026, 11, 15, 14, 30),
            },
            {
                "employee_id": emp_objs["EMP-1008"].id,  # David
                "leave_type": "Sick",
                "start_date": date(2026, 11, 10),
                "end_date": date(2026, 11, 11),
                "days_requested": 2.0,
                "reason": "Seasonal viral fever and medical recovery",
                "status": "Approved",
                "reviewed_by_id": emp_objs["EMP-1001"].id,
                "review_notes": "Approved. Take care and get well soon.",
                "reviewed_at": datetime(2026, 11, 10, 9, 15),
            },
            {
                "employee_id": emp_objs["EMP-1011"].id,  # James Wilson
                "leave_type": "Earned",
                "start_date": date(2026, 12, 1),
                "end_date": date(2026, 12, 5),
                "days_requested": 5.0,
                "reason": "Annual family vacation travel",
                "status": "Pending",
                "reviewed_by_id": None,
                "review_notes": None,
                "reviewed_at": None,
            },
            {
                "employee_id": emp_objs["EMP-1014"].id,  # Maya Patel
                "leave_type": "Casual",
                "start_date": date(2026, 11, 28),
                "end_date": date(2026, 11, 28),
                "days_requested": 1.0,
                "reason": "Relocation moving day and house utilities setup",
                "status": "Pending",
                "reviewed_by_id": None,
                "review_notes": None,
                "reviewed_at": None,
            },
            {
                "employee_id": emp_objs["EMP-1009"].id,  # Priya Sharma
                "leave_type": "Sick",
                "start_date": date(2026, 10, 18),
                "end_date": date(2026, 10, 19),
                "days_requested": 2.0,
                "reason": "Severe headache and eye strain",
                "status": "Approved",
                "reviewed_by_id": emp_objs["EMP-1001"].id,
                "review_notes": "Approved retrospectively.",
                "reviewed_at": datetime(2026, 10, 20, 10, 0),
            },
        ]
        for req in sample_requests:
            db.add(LeaveRequest(**req))

        # 5. Attendance Records (Last 14 business days)
        today = date(2026, 11, 20)
        statuses_pool = ["Present", "Present", "Present", "Remote", "Remote", "Late"]
        for emp in all_employees:
            for day_offset in range(14, -1, -1):
                cur_date = today - timedelta(days=day_offset)
                # Skip weekends (Saturday=5, Sunday=6)
                if cur_date.weekday() >= 5:
                    continue

                # Add some realistic variance
                dice = random.random()
                if dice < 0.65:
                    status = "Present"
                    check_in = f"08:{random.randint(45, 59):02d}"
                    check_out = f"17:{random.randint(45, 59):02d}"
                    working_hours = round(8.5 + random.uniform(0, 0.7), 2)
                elif dice < 0.85:
                    status = "Remote"
                    check_in = f"09:{random.randint(0, 10):02d}"
                    check_out = f"18:{random.randint(0, 20):02d}"
                    working_hours = round(8.0 + random.uniform(0, 0.5), 2)
                elif dice < 0.95:
                    status = "Late"
                    check_in = f"10:{random.randint(15, 45):02d}"
                    check_out = f"18:{random.randint(30, 59):02d}"
                    working_hours = round(7.5 + random.uniform(0, 0.4), 2)
                else:
                    status = "Absent"
                    check_in = None
                    check_out = None
                    working_hours = 0.0

                att = AttendanceRecord(
                    employee_id=emp.id,
                    date=cur_date,
                    check_in=check_in,
                    check_out=check_out,
                    status=status,
                    working_hours=working_hours,
                    notes="Automated biometric scan" if status != "Absent" else "Unplanned absence",
                )
                db.add(att)

        # 6. Salary Structures & Payroll
        base_salaries = {
            "EMP-1001": 13500.0,  # VP Eng
            "EMP-1002": 12000.0,  # Head of Prod
            "EMP-1003": 11000.0,  # Dir People
            "EMP-1004": 12500.0,  # VP Sales
            "EMP-1005": 10500.0,  # Finance Controller
            "EMP-1006": 9800.0,   # Lead Arch
            "EMP-1007": 8500.0,   # Sr FullStack
            "EMP-1008": 7200.0,   # Frontend
            "EMP-1009": 7800.0,   # SRE
            "EMP-1010": 8200.0,   # Lead Designer
            "EMP-1011": 5800.0,   # Assoc PM
            "EMP-1012": 6200.0,   # Talent Spec
            "EMP-1013": 4500.0,   # People Ops
            "EMP-1014": 8000.0,   # Enterprise AE
            "EMP-1015": 5600.0,   # Growth Mkt
        }

        for emp in all_employees:
            base = base_salaries.get(emp.emp_code, 6000.0)
            housing = round(base * 0.15, 2)
            transport = 350.0
            other = 250.0
            pf_rate = 0.05
            tax_rate = 0.12 if base > 8000 else 0.08
            std_ded = 150.0

            sal_struct = SalaryStructure(
                employee_id=emp.id,
                base_salary=base,
                housing_allowance=housing,
                transport_allowance=transport,
                other_allowances=other,
                pf_rate=pf_rate,
                tax_rate=tax_rate,
                standard_deductions=std_ded,
                effective_date=date(2026, 1, 1),
            )
            db.add(sal_struct)

            # Generate Payroll for September and October 2026
            for pay_month, p_date in [("2026-09", date(2026, 9, 30)), ("2026-10", date(2026, 10, 31))]:
                allowances = housing + transport + other
                bonus = 500.0 if emp.emp_code in ["EMP-1007", "EMP-1014"] and pay_month == "2026-10" else 0.0
                gross = base + allowances + bonus
                pf_amt = round(base * pf_rate, 2)
                tax_amt = round(gross * tax_rate, 2)
                total_ded = round(pf_amt + tax_amt + std_ded, 2)
                net = round(gross - total_ded, 2)

                pr = PayrollRecord(
                    employee_id=emp.id,
                    pay_period=pay_month,
                    payment_date=p_date,
                    base_salary=base,
                    total_allowances=allowances,
                    bonuses=bonus,
                    gross_pay=gross,
                    pf_deduction=pf_amt,
                    tax_deduction=tax_amt,
                    other_deductions=std_ded,
                    total_deductions=total_ded,
                    net_pay=net,
                    status="Paid",
                    payment_method="Direct Deposit",
                    notes=f"Monthly payroll for {pay_month}",
                )
                db.add(pr)

        # 7. Projects
        projects_data = [
            {
                "name": "Apollo Cloud & Multi-Region Migration",
                "code": "PRJ-APOLLO",
                "description": "Migrating monolithic services to containerized microservices on Kubernetes across US-East and EU-West.",
                "status": "In Progress",
                "priority": "Critical",
                "lead_id": emp_objs["EMP-1006"].id,  # Marcus Vance
                "start_date": date(2026, 8, 1),
                "target_date": date(2026, 12, 15),
                "budget": 125000.0,
            },
            {
                "name": "WorkSphere Mobile Companion v2",
                "code": "PRJ-MOBILE",
                "description": "Next-gen cross-platform mobile client for employee attendance check-ins, leave approvals, and push alerts.",
                "status": "In Progress",
                "priority": "High",
                "lead_id": emp_objs["EMP-1010"].id,  # Zoe Martinez
                "start_date": date(2026, 9, 1),
                "target_date": date(2026, 12, 30),
                "budget": 85000.0,
            },
            {
                "name": "Global Talent Expansion & Onboarding Hub",
                "code": "PRJ-TALENT",
                "description": "Scale hiring pipeline for 30+ new international technical roles with automated onboarding checklists.",
                "status": "In Progress",
                "priority": "Medium",
                "lead_id": emp_objs["EMP-1003"].id,  # Rachel Adams
                "start_date": date(2026, 10, 1),
                "target_date": date(2027, 2, 28),
                "budget": 60000.0,
            },
            {
                "name": "SOC-2 Type II Security Compliance Audit",
                "code": "PRJ-SOC2",
                "description": "Comprehensive security governance audit, automated evidence collection, and penetration testing verification.",
                "status": "Completed",
                "priority": "Critical",
                "lead_id": emp_objs["EMP-1009"].id,  # Priya Sharma
                "start_date": date(2026, 6, 1),
                "target_date": date(2026, 10, 31),
                "budget": 50000.0,
            },
            {
                "name": "Enterprise Client Billing & CRM Overhaul",
                "code": "PRJ-BILLING",
                "description": "Automated usage-based invoice generation and integration with enterprise Stripe Billing & Salesforce.",
                "status": "Planning",
                "priority": "Medium",
                "lead_id": emp_objs["EMP-1002"].id,  # Alex Chen
                "start_date": date(2026, 11, 15),
                "target_date": date(2027, 3, 31),
                "budget": 75000.0,
            },
        ]

        proj_objs = {}
        for p in projects_data:
            proj = Project(**p)
            db.add(proj)
            proj_objs[p["code"]] = proj
        db.flush()

        # Project Memberships
        memberships = [
            # Apollo
            (proj_objs["PRJ-APOLLO"].id, emp_objs["EMP-1006"].id, "Tech Lead & Architect"),
            (proj_objs["PRJ-APOLLO"].id, emp_objs["EMP-1007"].id, "Backend Systems Engineer"),
            (proj_objs["PRJ-APOLLO"].id, emp_objs["EMP-1009"].id, "DevOps / Infrastructure"),
            # Mobile
            (proj_objs["PRJ-MOBILE"].id, emp_objs["EMP-1010"].id, "Lead Product Designer"),
            (proj_objs["PRJ-MOBILE"].id, emp_objs["EMP-1008"].id, "Mobile/Frontend Engineer"),
            (proj_objs["PRJ-MOBILE"].id, emp_objs["EMP-1011"].id, "Product Owner"),
            # Talent
            (proj_objs["PRJ-TALENT"].id, emp_objs["EMP-1003"].id, "Executive Sponsor"),
            (proj_objs["PRJ-TALENT"].id, emp_objs["EMP-1012"].id, "Talent Lead"),
            (proj_objs["PRJ-TALENT"].id, emp_objs["EMP-1013"].id, "Coordinator"),
            # SOC2
            (proj_objs["PRJ-SOC2"].id, emp_objs["EMP-1009"].id, "Compliance Lead"),
            (proj_objs["PRJ-SOC2"].id, emp_objs["EMP-1006"].id, "Security Reviewer"),
        ]
        for pid, eid, role in memberships:
            db.add(ProjectMember(project_id=pid, employee_id=eid, role_in_project=role))

        # 8. Project Tasks & Milestones
        tasks_data = [
            # Apollo tasks
            {
                "project_id": proj_objs["PRJ-APOLLO"].id,
                "title": "Provision Terraform EKS clusters in EU-West",
                "description": "Establish multi-AZ Kubernetes cluster with ingress controllers and Vault secrets injection.",
                "status": "Done",
                "priority": "Critical",
                "assigned_to_id": emp_objs["EMP-1009"].id,
                "milestone_name": "Phase 1: Multi-Region Infrastructure",
                "estimated_hours": 24.0,
                "due_date": date(2026, 9, 20),
                "completed_at": datetime(2026, 9, 18, 16, 0),
            },
            {
                "project_id": proj_objs["PRJ-APOLLO"].id,
                "title": "Migrate PostgreSQL database to Aurora Multi-Region",
                "description": "Execute zero-downtime database replication and cutover to AWS Aurora global cluster.",
                "status": "In Progress",
                "priority": "Critical",
                "assigned_to_id": emp_objs["EMP-1006"].id,
                "milestone_name": "Phase 2: Database Migration",
                "estimated_hours": 32.0,
                "due_date": date(2026, 11, 28),
                "completed_at": None,
            },
            {
                "project_id": proj_objs["PRJ-APOLLO"].id,
                "title": "Decouple notification service into event-driven Kafka workers",
                "description": "Extract asynchronous email, SMS, and webhook delivery into autonomous microservice.",
                "status": "In Progress",
                "priority": "High",
                "assigned_to_id": emp_objs["EMP-1007"].id,
                "milestone_name": "Phase 3: Service Decoupling",
                "estimated_hours": 20.0,
                "due_date": date(2026, 12, 5),
                "completed_at": None,
            },
            {
                "project_id": proj_objs["PRJ-APOLLO"].id,
                "title": "Conduct load testing and chaos monkey failover simulation",
                "description": "Simulate region outage and verify automatic latency-based DNS failover within 45s SLA.",
                "status": "To Do",
                "priority": "High",
                "assigned_to_id": emp_objs["EMP-1009"].id,
                "milestone_name": "Phase 4: Resilience & Verification",
                "estimated_hours": 16.0,
                "due_date": date(2026, 12, 12),
                "completed_at": None,
            },

            # Mobile App tasks
            {
                "project_id": proj_objs["PRJ-MOBILE"].id,
                "title": "Finalize design system Figma components & token export",
                "description": "Typography, button states, dark mode tokens, and navigation drawer layout specifications.",
                "status": "Done",
                "priority": "High",
                "assigned_to_id": emp_objs["EMP-1010"].id,
                "milestone_name": "Milestone: Design Hand-off",
                "estimated_hours": 18.0,
                "due_date": date(2026, 9, 30),
                "completed_at": datetime(2026, 9, 29, 17, 30),
            },
            {
                "project_id": proj_objs["PRJ-MOBILE"].id,
                "title": "Implement biometric quick check-in authentication screen",
                "description": "FaceID / TouchID biometric login with instant geofenced check-in ping to HR service.",
                "status": "In Progress",
                "priority": "Critical",
                "assigned_to_id": emp_objs["EMP-1008"].id,
                "milestone_name": "Milestone: Core App Features",
                "estimated_hours": 28.0,
                "due_date": date(2026, 11, 26),
                "completed_at": None,
            },
            {
                "project_id": proj_objs["PRJ-MOBILE"].id,
                "title": "Push notifications for leave approvals and task mentions",
                "description": "Integrate Firebase Cloud Messaging with background handler for real-time manager alerts.",
                "status": "Blocked",
                "priority": "Medium",
                "assigned_to_id": emp_objs["EMP-1008"].id,
                "milestone_name": "Milestone: Core App Features",
                "estimated_hours": 14.0,
                "due_date": date(2026, 12, 2),
                "completed_at": None,
            },
            {
                "project_id": proj_objs["PRJ-MOBILE"].id,
                "title": "User acceptance testing with 15 pilot employee testers",
                "description": "Coordinate Beta TestFlight distribution and gather structured UX feedback surveys.",
                "status": "To Do",
                "priority": "Medium",
                "assigned_to_id": emp_objs["EMP-1011"].id,
                "milestone_name": "Milestone: Beta Release",
                "estimated_hours": 12.0,
                "due_date": date(2026, 12, 18),
                "completed_at": None,
            },

            # Talent Expansion tasks
            {
                "project_id": proj_objs["PRJ-TALENT"].id,
                "title": "Draft and benchmark compensation bands for APAC hires",
                "description": "Aggregate Radford data to establish competitive market pay bands across Singapore and India.",
                "status": "Done",
                "priority": "High",
                "assigned_to_id": emp_objs["EMP-1003"].id,
                "milestone_name": "Milestone: Compensation Alignment",
                "estimated_hours": 15.0,
                "due_date": date(2026, 10, 20),
                "completed_at": datetime(2026, 10, 19, 11, 0),
            },
            {
                "project_id": proj_objs["PRJ-TALENT"].id,
                "title": "Launch targeted LinkedIn & Greenhouse recruiting campaigns",
                "description": "Publish 12 critical roles with screening scorecards for Engineering and Product.",
                "status": "In Progress",
                "priority": "High",
                "assigned_to_id": emp_objs["EMP-1012"].id,
                "milestone_name": "Milestone: Candidate Sourcing",
                "estimated_hours": 20.0,
                "due_date": date(2026, 11, 30),
                "completed_at": None,
            },
            {
                "project_id": proj_objs["PRJ-TALENT"].id,
                "title": "Automate welcome equipment shipment and onboarding portal credentials",
                "description": "Connect HRIS trigger to IT hardware provisioning and SSO credential creation.",
                "status": "To Do",
                "priority": "Medium",
                "assigned_to_id": emp_objs["EMP-1013"].id,
                "milestone_name": "Milestone: Onboarding Automation",
                "estimated_hours": 16.0,
                "due_date": date(2026, 12, 15),
                "completed_at": None,
            },

            # SOC2 tasks
            {
                "project_id": proj_objs["PRJ-SOC2"].id,
                "title": "Complete third-party network penetration test report",
                "description": "Resolve all medium and high severity findings with audited re-test signoff.",
                "status": "Done",
                "priority": "Critical",
                "assigned_to_id": emp_objs["EMP-1009"].id,
                "milestone_name": "Milestone: External Audit Signoff",
                "estimated_hours": 40.0,
                "due_date": date(2026, 10, 25),
                "completed_at": datetime(2026, 10, 24, 18, 0),
            },
        ]

        for t in tasks_data:
            db.add(ProjectTask(**t))

        db.flush()
        print("Database successfully seeded with realistic sample data!")


if __name__ == "__main__":
    seed_database(force_reseed=True)
