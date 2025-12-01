import random
import re
from collections import defaultdict

class MarkovPasswordGenerator:
    """
    Генератор паролей на основе Марковских цепей.
    """

    def __init__(self, corpus_file_path: str, chain_order: int = 2):
        self.corpus_file_path = corpus_file_path
        self.chain_order = chain_order
        self.model = defaultdict(list)
        self._build_model()

    def _preprocess_text(self, text: str) -> str:
        cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]', '', text)
        return cleaned_text.lower()

    def _build_model(self):
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

        for i in range(len(clean_text) - self.chain_order):
            state = clean_text[i:i + self.chain_order]
            next_char = clean_text[i + self.chain_order]
            self.model[state].append(next_char)

        print(f"Модель построена. Найдено {len(self.model)} состояний.")

    def generate(self, length: int = 12) -> str:
        if not self.model:
            return "Ошибка: модель не построена"

        # --- 1. Генерация словоподобной основы ---
        start_state = random.choice(list(self.model.keys()))
        password_base = start_state

        while len(password_base) < length - 2:
            current_state = password_base[-self.chain_order:]
            if current_state not in self.model:
                break
            password_base += random.choice(self.model[current_state])

        print(f"\n🔹 Основа слова: {password_base}")

        # --- 2. Добавляем два спецсимвола ---
        symbols = "!@#$%^&*"
        digits = "0123456789"

        password_with_symbols = password_base
        for _ in range(2):
            char_to_add = random.choice(symbols + digits)
            pos = random.randint(1, len(password_with_symbols) - 1)
            password_with_symbols = (
                password_with_symbols[:pos] +
                char_to_add +
                password_with_symbols[pos:]
            )

        print(f"🔸 После добавления символов: {password_with_symbols}")

        # --- 3. Финальная обработка ---
        final_password = password_with_symbols[:length].capitalize()

        print(f"🔻 Финальный пароль: {final_password}")

        return final_password


# --- Пример ---
if __name__ == "__main__":
    gen = MarkovPasswordGenerator("corpus.txt", chain_order=3)
    print("\n--- Генерация ---")
    for _ in range(3):
        gen.generate(length=14)
