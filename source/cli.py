import typer
import getpass
import pyperclip 
import os
from source.generator import MarkovPasswordGenerator
from source.vault import PasswordVault
from typing import Annotated, Optional
from pathlib import Path

# Импортируем пути к данным
from source import CORPUS_PATH, MODEL_PATH, PACKAGE_DATA_DIR

# Создаем приложение Typer
app = typer.Typer(help="Менеджер паролей с генератором на основе цепей Маркова.")

# --- Вспомогательная функция для получения Master-ключа ---
def _get_vault() -> Optional[PasswordVault]:
    """Запрашивает мастер-пароль и инициализирует хранилище."""
    try:
        master_password = getpass.getpass("Введите МАСТЕР-ПАРОЛЬ: ")
        if not master_password:
            typer.secho("Мастер-пароль не может быть пустым.", fg=typer.colors.RED)
            return None
        return PasswordVault(master_password)
    except FileNotFoundError:
        typer.secho(" Ошибка при инициализации хранилища. Проверьте правильность пути или убедитесь, что файлы vault.py и key.salt доступны.", fg=typer.colors.RED)
        return None
    except Exception as e:
        typer.secho(" Неверный МАСТЕР-ПАРОЛЬ или поврежден файл ключа.", fg=typer.colors.RED)
        return None

# --- КОМАНДЫ ---

@app.command()
def generate(
    length: int = typer.Option(16, "--length", "-l", help="Длина пароля"),
    count: int = typer.Option(1, "--count", "-c", help="Количество паролей"),
    corpus: str = typer.Option(str(CORPUS_PATH), help="Путь к файлу с текстом"),
    service: Annotated[Optional[str], typer.Option("--save", help="Имя сервиса, куда сохранить пароль.")] = None,
):
    """
    Генерирует один или несколько паролей и опционально сохраняет их.
    """
    if not 1 <= length <= 1000:
        raise typer.BadParameter("Длина (length) должна быть в диапазоне 1–1000.")
    if not 1 <= count <= 100:
        raise typer.BadParameter("Количество (count) должно быть в диапазоне 1–100.")

    try:
        # Генератор сам решит, загружать модель или строить её
        gen = MarkovPasswordGenerator(corpus_file_path=corpus)
        typer.secho(f"\nГенерируем {count} пароль(ей) длиной {length}...", fg=typer.colors.BLUE)
        
        generated_passwords = []
        for _ in range(count):
            pwd = gen.generate(length=length)
            typer.secho(f"   {pwd}", fg=typer.colors.GREEN, bold=True)
            generated_passwords.append(pwd)
            
        typer.echo("")
        
        if service and generated_passwords:
            if count > 1:
                typer.secho(" Сохраняется только первый сгенерированный пароль.", fg=typer.colors.YELLOW)
                pwd_to_save = generated_passwords[0]
            else:
                pwd_to_save = generated_passwords[0]

            username = typer.prompt(f"Введите имя пользователя (логин/email) для сервиса '{service}'")
            vault = _get_vault()
            
            if vault:
                vault.add_password(service, username, pwd_to_save)
                typer.secho(f" Пароль для '{service}' сохранен в зашифрованном виде.", fg=typer.colors.GREEN)
                pyperclip.copy(pwd_to_save)
                typer.secho(" Сгенерированный пароль скопирован в буфер обмена.", fg=typer.colors.CYAN)

    except FileNotFoundError as e:
        typer.secho(f"Ошибка: {e}", fg=typer.colors.RED)
        typer.echo(f"Проверьте наличие файла корпуса. Он должен быть здесь: {CORPUS_PATH}")
    except Exception as e:
        typer.secho(f"Произошла непредвиденная ошибка: {e}", fg=typer.colors.RED)


@app.command()
def train(
    corpus: str = typer.Option(str(CORPUS_PATH), help="Путь к новому тексту")
):
    """
    Принудительно переобучает модель (если вы изменили текст в corpus.txt).
    """
    if MODEL_PATH.exists():
        MODEL_PATH.unlink() # Используем pathlib для удаления
        typer.secho("Старая модель удалена.", fg=typer.colors.YELLOW)
    
    try:
        # Принудительно запускает перестроение модели
        gen = MarkovPasswordGenerator(corpus_file_path=corpus, force_rebuild=True)
        typer.secho(" Модель успешно переобучена и сохранена!", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Ошибка обучения: {e}", fg=typer.colors.RED)

@app.command()
def add(
    service: Annotated[str, typer.Argument(help="Имя сервиса (например, facebook.com)")],
    username: Annotated[str, typer.Argument(help="Логин/Email для сервиса")]
):
    """
    Добавляет или обновляет пароль в защищенном хранилище.
    Пароль запрашивается вручную (скрытый ввод).
    """
    vault = _get_vault()
    if vault:
        plaintext_password = getpass.getpass(f"Введите пароль для {service} (скрыто): ")
        if not plaintext_password:
             typer.secho("Пароль не может быть пустым.", fg=typer.colors.RED)
             return

        vault.add_password(service, username, plaintext_password)
        typer.secho(f" Пароль для '{service}' успешно добавлен/обновлен.", fg=typer.colors.GREEN)

@app.command()
def get(
    service: Annotated[str, typer.Argument(help="Сервис, для которого нужно получить пароль")],
    copy: Annotated[bool, typer.Option("--copy", "-c", help="Скопировать пароль в буфер обмена")] = False
):
    """
    Получает пароль по имени сервиса.
    """
    vault = _get_vault()
    if not vault:
        return

    result = vault.get_password(service)
    
    if result:
        username, password = result
        typer.secho(f"\n Сервис: {service}", fg=typer.colors.BLUE)
        typer.secho(f"   Логин: {username}", fg=typer.colors.WHITE)
        
        if copy:
            pyperclip.copy(password)
            typer.secho("   Пароль: ******** (скопирован в буфер обмена)", fg=typer.colors.GREEN)
        else:
            typer.secho(f"   Пароль: {password}", fg=typer.colors.YELLOW, bold=True)
            
    else:
        typer.secho(f" Сервис '{service}' не найден или неверный мастер-пароль.", fg=typer.colors.RED)


@app.command()
def delete(
    service: Annotated[str, typer.Argument(help="Сервис, для которого нужно удалить пароль")]
):
    """
    Удаляет пароль для указанного сервиса из хранилища.
    """
    vault = _get_vault()
    if not vault:
        return
    
    confirm = typer.confirm(f" Вы уверены, что хотите удалить пароль для '{service}'?")
    if not confirm:
        typer.secho("Отменено.", fg=typer.colors.YELLOW)
        return
    
    if vault.delete_password(service):
        typer.secho(f" Пароль для '{service}' успешно удален.", fg=typer.colors.GREEN)
    else:
        typer.secho(f" Сервис '{service}' не найден в базе данных.", fg=typer.colors.RED)


@app.command()
def reset(
    force: Annotated[bool, typer.Option("--force", "-f", help="Пропустить подтверждение")] = False
):
    """
    Удаляет ВСЕ пароли из хранилища. ВНИМАНИЕ: это необратимая операция!
    """
    vault = _get_vault()
    if not vault:
        return
    
    if not force:
        typer.secho("\n ВНИМАНИЕ ", fg=typer.colors.RED, bold=True)
        typer.secho("Эта операция удалит ВСЕ сохраненные пароли!", fg=typer.colors.RED)
        typer.secho("Это действие НЕОБРАТИМО!\n", fg=typer.colors.RED)
        
        confirm1 = typer.confirm("Вы действительно хотите продолжить?")
        if not confirm1:
            typer.secho("Отменено.", fg=typer.colors.YELLOW)
            return
        
        confirm2 = typer.confirm("Последнее подтверждение. Удалить ВСЕ пароли?")
        if not confirm2:
            typer.secho("Отменено.", fg=typer.colors.YELLOW)
            return
    
    vault.reset_vault()
    typer.secho("Все пароли успешно удалены из хранилища.", fg=typer.colors.GREEN)
    typer.secho("База данных очищена.", fg=typer.colors.CYAN)


@app.command(name="list")
def list_passwords():
    """
    Отображает список всех сервисов, для которых сохранены пароли.
    """
    vault = _get_vault()
    if not vault:
        return
        
    services = vault.list_services()
    if services:
        typer.secho("\n Сохраненные сервисы:", fg=typer.colors.MAGENTA)
        for svc in services:
            typer.echo(f"   - {svc}")
    else:
        typer.secho("База данных пуста.", fg=typer.colors.YELLOW)

if __name__ == "__main__":
    app()