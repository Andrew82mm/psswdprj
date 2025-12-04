import random
import re
from collections import defaultdict
from functools import lru_cache


def random_capitalize(s: str, probability: float = 0.3) -> str:
    """
    Делает случайные буквы заглавными с указанной вероятностью.
    """
    result = []
    for ch in s:
        if ch.isalpha() and random.random() < probability:
            result.append(ch.upper())
        else:
            result.append(ch)
    return "".join(result)


class MarkovPasswordGenerator:
    """
    Генератор паролей на основе Марковских цепей.
    """

    def __init__(self, corpus_file_path: str, chain_order: int = 2):
        self.corpus_file_path = corpus_file_path
        self.chain_order = chain_order
        self.model = defaultdict(list)
        self.start_states = []       # список "хороших" стартовых состояний
        self._build_model()

    @staticmethod
    @lru_cache(maxsize=8)
    def _preprocess_text(text: str) -> str:
        """
        Очищает текст, оставляя только буквы (кириллица и латиница).
        Использует кэширование для ускорения.
        """
        # Удаляем всё, что НЕ буква
        cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]', '', text)
        return cleaned_text.lower()

    def _build_model(self):
        """Строит модель Марковской цепи из очищенного текста."""
        print("Построение модели из текстового файла...")

        try:
            with open(self.corpus_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except FileNotFoundError:
            print(f"Ошибка: Файл не найден по пути {self.corpus_file_path}")
            return

        clean_text = self._preprocess_text(text)
        if not clean_text:
            print("Ошибка: После очистки текста не осталось символов.")
            return

        N = self.chain_order

        # Строим модель
        for i in range(len(clean_text) - N):
            state = clean_text[i:i + N]
            next_char = clean_text[i + N]
            self.model[state].append(next_char)

        # Подготовка стартовых состояний — первые символы слов
        # (улучшает "словоподобность")
        self.start_states = [
            clean_text[i:i + N]
            for i in range(len(clean_text) - N)
            if i == 0 or clean_text[i - 1] == ' '
        ]

        # fallback если нет пробелов
        if not self.start_states:
            self.start_states = list(self.model.keys())

        print(f"Модель построена. {len(self.model)} уникальных состояний.")

    def generate(self, length: int = 12) -> str:
        """
        Генерирует словоподобный пароль.
        Интерфейс полностью сохранён.
        """
        if not self.model:
            return "Ошибка: Модель не построена."

        # 1. Выбираем начальное состояние
        # (теперь предпочтительно начало строки/слова)
        start_state = random.choice(self.start_states)
        password_base = start_state

        # 2. Генерация символов
        while len(password_base) < length:
            state = password_base[-self.chain_order:]
            next_chars = self.model.get(state)

            if not next_chars:
                # fallback: выбрать случайное состояние и продолжить
                state = random.choice(list(self.model.keys()))
                next_chars = self.model[state]

            password_base += random.choice(next_chars)

        # 3. Случайные заглавные буквы
        final_password = random_capitalize(password_base[:length])

        return final_password


# --- Проверка ---
if __name__ == "__main__":
    generator = MarkovPasswordGenerator('corpus.txt', chain_order=2)

    print("\n--- Сгенерированные пароли ---")
    for _ in range(5):
        print(generator.generate(length=15))
