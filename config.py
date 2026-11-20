"""
WorkSphere HR - Global Configuration
Supports switching between SQLite and PostgreSQL via the DATABASE_URL environment variable.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Database configuration
# Can be overridden via environment variable:
# e.g., DATABASE_URL=postgresql://user:password@localhost:5432/worksphere_hr
DEFAULT_SQLITE_PATH = BASE_DIR / "worksphere.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")

# App Settings
APP_NAME = "WorkSphere HR & Projects"
APP_TAGLINE = "Intelligent Human Capital & Project Management Suite"
APP_ICON = "💼"
CURRENCY_SYMBOL = "$"

# Leave Policy Defaults (Annual Allowance in days)
LEAVE_DEFAULTS = {
    "casual_leave": 10.0,
    "sick_leave": 10.0,
    "earned_leave": 15.0,
}

# Standard Payroll Deductions
DEFAULT_PF_RATE = 0.05       # 5% Provident Fund
DEFAULT_TAX_RATE = 0.10      # 10% Standard Withholding Tax
DEFAULT_STANDARD_DEDUCTION = 150.0  # Professional tax/insurance
