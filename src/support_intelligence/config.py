from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
SQL_OUTPUT_DIR = OUTPUTS_DIR / "sql"
EVALUATION_DIR = OUTPUTS_DIR / "evaluation"
MODELS_DIR = OUTPUTS_DIR / "models"
SQL_DIR = PROJECT_ROOT / "sql"
APP_DIR = PROJECT_ROOT / "app"
DB_PATH = WAREHOUSE_DIR / "support_intelligence.db"


def ensure_project_directories() -> None:
    for directory in [
        RAW_DATA_DIR,
        WAREHOUSE_DIR,
        OUTPUTS_DIR,
        FIGURES_DIR,
        TABLES_DIR,
        SQL_OUTPUT_DIR,
        EVALUATION_DIR,
        MODELS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

