import random
import re
from collections import defaultdict

class MarkovPasswordGenerator:
    """
    Генератор паролей на основе Марковских цепей.
    Анализирует текстовый файл для создания "словоподобных" паролей.
    """

    def __init__(self, corpus_file_path: str, chain_order: int = 2):
        """
        Инициализация генератора.
        :param corpus_file_path: Путь к текстовому файлу для обучения.
        :param chain_order: Порядок цепи (сколько предыдущих символов учитывать).
        """
        self.corpus_file_path = corpus_file_path
        self.chain_order = chain_order
        self.model = defaultdict(list)
        self._build_model()

    def _preprocess_text(self, text: str) -> str:
        """
        Очищает текст, оставляя только буквы (кириллицу и латиницу) и переводя в нижний регистр.
        Это ключевой шаг для получения качественных паролей.
        """
        # Удаляем все, что НЕ является буквой (ни кириллицей, ни латиницей)
        # [^a-zA-Zа-яА-ЯёЁ] - это регулярное выражение, означающее "любой символ, кроме..."
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

        # 1. Очищаем текст перед построением модели
        clean_text = self._preprocess_text(text)

        if not clean_text:
            print("Ошибка: После очистки текста не осталось символов. Проверьте файл корпуса.")
            return

        # 2. Строим модель из очищенного текста
        for i in range(len(clean_text) - self.chain_order):
            state = clean_text[i:i + self.chain_order]
            next_char = clean_text[i + self.chain_order]
            self.model[state].append(next_char)
        
        print(f"Модель построена. Найдено {len(self.model)} уникальных состояний.")

    def generate(self, length: int = 12) -> str:
        """
        Генерирует "словоподобный" пароль заданной длины.
        """
        if not self.model:
            return "Ошибка: Модель не построена."

        # 1. Генерируем основу пароля - слово
        # Выбираем случайное начальное состояние, состоящее только из букв
        start_state = random.choice(list(self.model.keys()))
        password_base = start_state

        while len(password_base) < length - 2: # Оставляем место для символов
            current_state = password_base[-self.chain_order:]
            if current_state not in self.model:
                break
            next_char = random.choice(self.model[current_state])
            password_base += next_char

        # 2. Усиливаем пароль для надежности
        # Добавляем случайные цифры и символы
        symbols = "!@#$%^&*"
        digits = "0123456789"
        
        # Добавляем 2 случайных символа в случайные места
        for _ in range(2):
            char_to_add = random.choice(symbols + digits)
            insert_pos = random.randint(1, len(password_base) - 1)
            password_base = password_base[:insert_pos] + char_to_add + password_base[insert_pos:]
            
        # 3. Финальная обработка: делаем первую букву заглавной и обрезаем
        final_password = password_base[:length].capitalize()
        
        return final_password

# --- Пример использования ---
if __name__ == "__main__":
    # ВАЖНО: Убедись, что твой файл 'corpus.txt' содержит достаточно большой текст
    # на одном языке (например, только русский). Чем больше текст, тем лучше.
    # Удали из него лишние заголовки, оглавления и т.д.
    
    # Создаем экземпляр генератора
    generator = MarkovPasswordGenerator('corpus.txt', chain_order=2)

    # Генерируем несколько паролей
    print("\n--- Сгенерированные пароли ---")
    for _ in range(5):
        password = generator.generate(length=10)
        print(password)
