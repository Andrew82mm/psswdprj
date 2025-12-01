import typer
from generator import MarkovPasswordGenerator
import os

# Создаем приложение Typer
app = typer.Typer(help="Генератор надежных и произносимых паролей")

@app.command()
def generate(
    length: int = typer.Option(12, "--length", "-l", help="Длина пароля"),
    count: int = typer.Option(1, "--count", "-c", help="Количество паролей"),
    corpus: str = typer.Option("corpus.txt", help="Путь к файлу с текстом")
):
    if length <= 0:
        raise typer.BadParameter("length must be > 0")
    if count <= 0:
        raise typer.BadParameter("count must be > 0")
    
    """
    Генерирует один или несколько паролей.
    """
    try:
        # Инициализация генератора (автоматически подгрузит кэш или создаст его)
        gen = MarkovPasswordGenerator(corpus_file_path=corpus)
        
        typer.secho(f"\n Генерируем {count} пароль(ей) длиной {length}...", fg=typer.colors.BLUE)
        
        for _ in range(count):
            pwd = gen.generate(length=length)
            # Выводим пароль зеленым цветом (как в матрице)
            typer.secho(f"  {pwd}", fg=typer.colors.GREEN, bold=True)
            
        typer.echo("") # Отступ в конце
        
    except FileNotFoundError as e:
        typer.secho(f"Ошибка: {e}", fg=typer.colors.RED)
        typer.echo("Пожалуйста, создайте файл 'corpus.txt' с любым текстом (книгой) внутри.")

@app.command()
def train(
    corpus: str = typer.Option("corpus.txt", help="Путь к новому тексту")
):
    """
    Принудительно переобучает модель (если вы изменили текст в corpus.txt).
    """
    if os.path.exists("model.pkl"):
        os.remove("model.pkl")
        typer.secho("Старая модель удалена.", fg=typer.colors.YELLOW)
    
    try:
        gen = MarkovPasswordGenerator(corpus_file_path=corpus)
        typer.secho(" Модель успешно переобучена!", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Ошибка: {e}", fg=typer.colors.RED)

if __name__ == "__main__":
    app()