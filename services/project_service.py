"""
WorkSphere HR - Project Management Service
Business logic for projects, milestones, tasks, team allocation, and workload metrics.
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import joinedload
from db.connection import get_db
from db.models import Project, ProjectTask, ProjectMember, Employee, Department


def get_all_projects(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all projects with leader info and calculated progress metrics."""
    with get_db() as db:
        query = db.query(Project).options(
            joinedload(Project.lead),
            joinedload(Project.tasks),
            joinedload(Project.members).joinedload(ProjectMember.employee),
        )

        if status_filter and status_filter != "All":
            query = query.filter(Project.status == status_filter)

        if priority_filter and priority_filter != "All":
            query = query.filter(Project.priority == priority_filter)

        projects = query.order_by(Project.created_at.desc()).all()

        results = []
        for p in projects:
            total_tasks = len(p.tasks)
            done_tasks = sum(1 for t in p.tasks if t.status == "Done")
            in_prog_tasks = sum(1 for t in p.tasks if t.status == "In Progress")
            blocked_tasks = sum(1 for t in p.tasks if t.status == "Blocked")
            todo_tasks = sum(1 for t in p.tasks if t.status == "To Do")

            progress_pct = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

            results.append({
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "description": p.description or "",
                "status": p.status,
                "priority": p.priority,
                "lead_id": p.lead_id,
                "lead_name": p.lead.full_name if p.lead else "Unassigned",
                "start_date": p.start_date,
                "target_date": p.target_date,
                "budget": p.budget,
                "total_tasks": total_tasks,
                "done_tasks": done_tasks,
                "in_prog_tasks": in_prog_tasks,
                "blocked_tasks": blocked_tasks,
                "todo_tasks": todo_tasks,
                "progress_pct": progress_pct,
                "member_count": len(p.members),
            })
        return results


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """Get project by ID with members and tasks."""
    with get_db() as db:
        p = (
            db.query(Project)
            .options(
                joinedload(Project.lead),
                joinedload(Project.members).joinedload(ProjectMember.employee),
                joinedload(Project.tasks).joinedload(ProjectTask.assignee),
            )
            .filter(Project.id == project_id)
            .first()
        )
        if not p:
            return None

        total_tasks = len(p.tasks)
        done_tasks = sum(1 for t in p.tasks if t.status == "Done")
        progress_pct = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        return {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
            "status": p.status,
            "priority": p.priority,
            "lead_name": p.lead.full_name if p.lead else "None",
            "start_date": p.start_date,
            "target_date": p.target_date,
            "budget": p.budget,
            "progress_pct": progress_pct,
            "members": [
                {
                    "employee_id": m.employee_id,
                    "name": m.employee.full_name if m.employee else "Unknown",
                    "role": m.role_in_project,
                }
                for m in p.members
            ],
        }


def create_project(
    name: str,
    code: str,
    description: str,
    status: str,
    priority: str,
    lead_id: Optional[int],
    start_date: date,
    target_date: date,
    budget: float = 0.0,
) -> Tuple[bool, str, Optional[int]]:
    """Validate and create a new project."""
    if not name.strip():
        return False, "Project name cannot be empty.", None
    if not code.strip():
        return False, "Project code cannot be empty.", None
    if start_date > target_date:
        return False, "Start date cannot be after target date.", None

    clean_code = code.strip().upper()

    with get_db() as db:
        existing = db.query(Project).filter(Project.code == clean_code).first()
        if existing:
            return False, f"Project code '{clean_code}' is already in use.", None

        proj = Project(
            name=name.strip(),
            code=clean_code,
            description=description.strip(),
            status=status,
            priority=priority,
            lead_id=lead_id if lead_id else None,
            start_date=start_date,
            target_date=target_date,
            budget=budget,
            created_at=datetime.utcnow(),
        )
        db.add(proj)
        db.flush()
        pid = proj.id

    return True, f"Project '{name}' created successfully.", pid


def update_project(project_id: int, **kwargs) -> Tuple[bool, str]:
    """Update project metadata."""
    with get_db() as db:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return False, "Project not found."

        for key, val in kwargs.items():
            if hasattr(proj, key) and val is not None:
                setattr(proj, key, val)

    return True, "Project updated successfully."


def get_project_members(project_id: int) -> List[Dict[str, Any]]:
    """Get list of assigned team members for a project."""
    with get_db() as db:
        members = (
            db.query(ProjectMember)
            .options(joinedload(ProjectMember.employee).joinedload(Employee.department))
            .filter(ProjectMember.project_id == project_id)
            .all()
        )
        return [
            {
                "employee_id": m.employee_id,
                "name": m.employee.full_name if m.employee else "Unknown",
                "department": m.employee.department.name if m.employee and m.employee.department else "N/A",
                "role_in_project": m.role_in_project,
            }
            for m in members
        ]


def add_project_member(project_id: int, employee_id: int, role: str) -> Tuple[bool, str]:
    """Add an employee to a project team."""
    with get_db() as db:
        existing = (
            db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id, ProjectMember.employee_id == employee_id)
            .first()
        )
        if existing:
            existing.role_in_project = role
            return True, "Member role updated."

        member = ProjectMember(project_id=project_id, employee_id=employee_id, role_in_project=role)
        db.add(member)

    return True, "Member added to project."


def get_project_tasks(
    project_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    assignee_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve tasks with optional filters."""
    with get_db() as db:
        query = db.query(ProjectTask).options(
            joinedload(ProjectTask.project),
            joinedload(ProjectTask.assignee).joinedload(Employee.department),
        )

        if project_id:
            query = query.filter(ProjectTask.project_id == project_id)
        if status_filter and status_filter != "All":
            query = query.filter(ProjectTask.status == status_filter)
        if priority_filter and priority_filter != "All":
            query = query.filter(ProjectTask.priority == priority_filter)
        if assignee_id:
            query = query.filter(ProjectTask.assigned_to_id == assignee_id)

        tasks = query.order_by(ProjectTask.due_date.asc(), ProjectTask.id.desc()).all()

        results = []
        for t in tasks:
            results.append({
                "id": t.id,
                "project_id": t.project_id,
                "project_name": t.project.name if t.project else "Unassigned",
                "project_code": t.project.code if t.project else "",
                "title": t.title,
                "description": t.description or "",
                "status": t.status,
                "priority": t.priority,
                "assigned_to_id": t.assigned_to_id,
                "assignee_name": t.assignee.full_name if t.assignee else "Unassigned",
                "assignee_dept": t.assignee.department.name if t.assignee and t.assignee.department else "",
                "milestone_name": t.milestone_name or "General",
                "estimated_hours": t.estimated_hours,
                "due_date": t.due_date,
                "completed_at": t.completed_at,
                "created_at": t.created_at,
            })
        return results


def create_task(
    project_id: int,
    title: str,
    description: str,
    status: str = "To Do",
    priority: str = "Medium",
    assigned_to_id: Optional[int] = None,
    milestone_name: Optional[str] = None,
    estimated_hours: float = 8.0,
    due_date: Optional[date] = None,
) -> Tuple[bool, str, Optional[int]]:
    """Create a new project task or milestone item."""
    if not title.strip():
        return False, "Task title cannot be empty.", None

    if not due_date:
        due_date = date.today()

    with get_db() as db:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return False, "Invalid project ID.", None

        task = ProjectTask(
            project_id=project_id,
            title=title.strip(),
            description=description.strip() if description else "",
            status=status,
            priority=priority,
            assigned_to_id=assigned_to_id if assigned_to_id else None,
            milestone_name=milestone_name.strip() if milestone_name else "General",
            estimated_hours=float(estimated_hours),
            due_date=due_date,
            completed_at=datetime.utcnow() if status == "Done" else None,
            created_at=datetime.utcnow(),
        )
        db.add(task)
        db.flush()
        tid = task.id

    return True, f"Task '{title}' created successfully.", tid


def update_task_status(task_id: int, new_status: str) -> Tuple[bool, str]:
    """Transition task status (To Do, In Progress, Blocked, Done)."""
    valid_statuses = ["To Do", "In Progress", "Blocked", "Done"]
    if new_status not in valid_statuses:
        return False, f"Invalid status '{new_status}'."

    with get_db() as db:
        task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
        if not task:
            return False, "Task not found."

        task.status = new_status
        if new_status == "Done":
            task.completed_at = datetime.utcnow()
        else:
            task.completed_at = None

    return True, f"Task #{task_id} status updated to {new_status}."


def update_task(task_id: int, **kwargs) -> Tuple[bool, str]:
    """Update task fields."""
    with get_db() as db:
        task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
        if not task:
            return False, "Task not found."

        for key, val in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, val)

        if kwargs.get("status") == "Done" and not task.completed_at:
            task.completed_at = datetime.utcnow()

    return True, "Task updated successfully."


def get_project_metrics(project_id: int) -> Dict[str, Any]:
    """Calculate progress and task distribution for a single project."""
    tasks = get_project_tasks(project_id=project_id)
    total = len(tasks)
    done = sum(1 for t in tasks if t["status"] == "Done")
    in_prog = sum(1 for t in tasks if t["status"] == "In Progress")
    blocked = sum(1 for t in tasks if t["status"] == "Blocked")
    todo = sum(1 for t in tasks if t["status"] == "To Do")
    total_hours = sum(t["estimated_hours"] for t in tasks)

    return {
        "total_tasks": total,
        "done": done,
        "in_progress": in_prog,
        "blocked": blocked,
        "todo": todo,
        "progress_pct": round((done / total * 100), 1) if total > 0 else 0.0,
        "total_estimated_hours": total_hours,
    }


def get_workload_metrics() -> List[Dict[str, Any]]:
    """Calculate workload distribution and assigned tasks per employee."""
    with get_db() as db:
        employees = (
            db.query(Employee)
            .options(
                joinedload(Employee.department),
                joinedload(Employee.assigned_tasks),
            )
            .filter(Employee.is_active == True)
            .all()
        )

        workloads = []
        for emp in employees:
            tasks = emp.assigned_tasks
            total_tasks = len(tasks)
            if total_tasks == 0:
                continue

            open_tasks = sum(1 for t in tasks if t.status in ["To Do", "In Progress", "Blocked"])
            done_tasks = sum(1 for t in tasks if t.status == "Done")
            blocked_tasks = sum(1 for t in tasks if t.status == "Blocked")
            total_hours = sum(t.estimated_hours for t in tasks)
            open_hours = sum(t.estimated_hours for t in tasks if t.status != "Done")

            workloads.append({
                "employee_id": emp.id,
                "employee_name": emp.full_name,
                "role": emp.role,
                "department": emp.department.name if emp.department else "N/A",
                "total_tasks": total_tasks,
                "open_tasks": open_tasks,
                "done_tasks": done_tasks,
                "blocked_tasks": blocked_tasks,
                "open_hours": round(open_hours, 1),
                "total_hours": round(total_hours, 1),
            })

        workloads.sort(key=lambda x: x["open_tasks"], reverse=True)
        return workloads


def get_project_kpis() -> Dict[str, Any]:
    """Aggregate KPIs for executive dashboard."""
    with get_db() as db:
        total_projects = db.query(Project).count()
        active_projects = db.query(Project).filter(Project.status == "In Progress").count()
        total_tasks = db.query(ProjectTask).count()
        done_tasks = db.query(ProjectTask).filter(ProjectTask.status == "Done").count()
        blocked_tasks = db.query(ProjectTask).filter(ProjectTask.status == "Blocked").count()

        overall_completion = round((done_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

        return {
            "total_projects": total_projects,
            "active_projects": active_projects,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "blocked_tasks": blocked_tasks,
            "overall_completion_rate": overall_completion,
        }
