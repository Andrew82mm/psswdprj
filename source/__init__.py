# source/__init__.py

from pathlib import Path
from platformdirs import user_data_dir

# Определяем имя приложения и автора для создания уникальной папки
APP_NAME = "PasswordManager"
APP_AUTHOR = "Andrew"

# Получаем кросс-платформенный путь к директории данных пользователя
# На Linux: ~/.local/share/PasswordManager
# На macOS: ~/Library/Application Support/PasswordManager
# На Windows: C:\Users\<User>\AppData\Local\MyAppDev\PasswordManager
PACKAGE_DATA_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR))

# Создаем директорию, если она не существует
PACKAGE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Пути к файлам, создаваемым при работе приложения
MODEL_PATH = PACKAGE_DATA_DIR / "model.pkl"
# DB_PATH и SALT_PATH определяются в vault.py, но тоже используют PACKAGE_DATA_DIR

# --- Пути к данным ПАКЕТА (поставляемым с приложением) ---
PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True) # Создаем папку data, если ее нет

# Путь к корпусу текста, поставляемому с программой
CORPUS_PATH = DATA_DIR / "corpus.txt"