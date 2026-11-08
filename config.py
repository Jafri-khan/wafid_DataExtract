"""
Configuration settings and paths for the Wafid Medical Automation System.
"""
from pathlib import Path

# Base Paths
BASE_DIR = Path(r"F:\Datavalidation_Automation")
EXCEL_PATH = BASE_DIR / "Datatocheck.xlsx"
BACKUP_DIR = BASE_DIR / "backups"
LOG_DIR = BASE_DIR / "logs"
TESTS_DIR = BASE_DIR / "tests"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
EDGE_PROFILE_DIR = BASE_DIR / "edge_profile"

# Ensure directories exist
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
EDGE_PROFILE_DIR.mkdir(parents=True, exist_ok=True)

# URL Configuration
WAFID_BASE_URL = "https://wafid.com/en/"

# Automation Settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 15
HEADLESS_MODE = False

# Excel Column Mappings (1-indexed for openpyxl)
# Source Columns
COL_PASSPORT = 3  # Column C
COL_STATUS = 4    # Column D

# Destination Columns
COL_EXAM_DATE = 5   # Column E
COL_HEIGHT = 6      # Column F
COL_WEIGHT = 7      # Column G
COL_BLOOD = 8       # Column H
COL_HEMOGLOBIN = 9  # Column I
COL_RBS = 10        # Column J
COL_CREATININE = 11 # Column K
COL_REMARKS = 12    # Column L
