from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DATA_DIR = PACKAGE_ROOT / "data"  # Теперь внутри source

# Создаем директории при импорте, если их нет
DATA_DIR.mkdir(parents=True, exist_ok=True)