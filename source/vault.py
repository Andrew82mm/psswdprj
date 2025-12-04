import os
import sqlite3
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from typing import Optional

class PasswordVault:
    """Класс для управления зашифрованной базой паролей."""
    DB_PATH = 'passwords.db'
    SALT_PATH = 'key.salt' # Это не специальное расширений файлов, а просто набор сырых байтов, названо ради удобства
    ITERATIONS = 480000 # Рекомендованное количество итераций для KDF

    def __init__(self, master_password: str):
        self._conn = sqlite3.connect(self.DB_PATH)
        self._cursor = self._conn.cursor() # cursor — это объект, который выполняет SQL-запросы
        self._initialize_db()
        self._key = self._derive_key(master_password)
        self._fernet = Fernet(self._key)
        
    def _initialize_db(self):
        """Создает таблицу, если она не существует."""
        self._cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                id INTEGER PRIMARY KEY,
                service TEXT NOT NULL UNIQUE,
                username TEXT,
                encrypted_password TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def _get_salt(self, generate_if_missing: bool = True) -> bytes:
        """Получает или генерирует соль для KDF."""
        if os.path.exists(self.SALT_PATH):
            with open(self.SALT_PATH, 'rb') as f:
                return f.read()
        
        if generate_if_missing:
            # Генерация новой соли, если файл не найден
            salt = os.urandom(16)
            with open(self.SALT_PATH, 'wb') as f:
                f.write(salt)
            return salt
        
        raise FileNotFoundError("Файл соли не найден.")

    def _derive_key(self, master_password: str) -> bytes:
        """
        Использует PBKDF2 для получения криптографического ключа.
        """
        try:
            salt = self._get_salt()
        except FileNotFoundError:
             raise ValueError("Невозможно получить соль для генерации ключа.")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        # Ключ для Fernet должен быть base64-urlsafe
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key

    def add_password(self, service: str, username: str, plaintext_password: str):
        """Шифрует и сохраняет новый пароль в БД."""
        encrypted_data = self._fernet.encrypt(plaintext_password.encode())
        
        self._cursor.execute(
            "INSERT OR REPLACE INTO passwords (service, username, encrypted_password) VALUES (?, ?, ?)",
            # ? это placeholder (заполнитель) для значения, которое будет подставлено
            # Так же это выступает в роли защиты от SQL-инъекций, так так передаст данные отдельно, а не как часть SQL-кода
            (service.lower(), username, encrypted_data.decode())
        )
        self._conn.commit()
        
    def get_password(self, service: str) -> Optional[tuple[str, str]]:
        """Извлекает, расшифровывает и возвращает пароль."""
        self._cursor.execute(
            "SELECT username, encrypted_password FROM passwords WHERE service = ?",
            (service.lower(),)
        )
        row = self._cursor.fetchone()
        
        if row:
            username, encrypted_data = row
            try:
                decrypted_password = self._fernet.decrypt(encrypted_data.encode()).decode()
                return username, decrypted_password
            except Exception:
                # Ошибка расшифровки (скорее всего, неверный мастер-пароль)
                return None
        return None

    def delete_password(self, service: str) -> bool:
        """Удаляет пароль для указанного сервиса."""
        self._cursor.execute(
            "DELETE FROM passwords WHERE service = ?",
            (service.lower(),)
        )
        self._conn.commit()
        return self._cursor.rowcount > 0

    def reset_vault(self):
        """Удаляет все пароли из базы данных."""
        self._cursor.execute("DELETE FROM passwords")
        self._conn.commit()

    def list_services(self) -> list[str]:
        """Возвращает список всех сохраненных сервисов."""
        self._cursor.execute("SELECT service FROM passwords ORDER BY service")
        return [row[0] for row in self._cursor.fetchall()]

    def __del__(self):
        """Закрытие соединения с БД при удалении объекта."""
        self._conn.close()