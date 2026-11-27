"""Paths to source datasets and generated results."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

COMMITABLE_DATA_DIR = PROJECT_ROOT / "commitable_data"
RAWDATA_DIR = PROJECT_ROOT / "rawdata"
REFPRESS_DIR = PROJECT_ROOT / "refpress_data"
POWERBALANCE_DIR = PROJECT_ROOT / "powerbalance_data"
REFTHETA_DIR = PROJECT_ROOT / "target_thetas"
REF_U_DIR = PROJECT_ROOT / "target_u"
VALID_DIR = PROJECT_ROOT / "exp_pressures"

# Current input; switch to RAWDATA_DIR or REFPRESS_DIR for the full datasets.
DATA_DIR = COMMITABLE_DATA_DIR

CSV_DIR = PROJECT_ROOT / "csv_files"
FIGURES_DIR = PROJECT_ROOT / "figures"

