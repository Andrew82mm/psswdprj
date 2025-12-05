# source/generator.py

import random
import re
import pickle  # <-- Импортируем pickle
from collections import defaultdict
from functools import lru_cache
from pathlib import Path # <-- Импортируем Path

# Импортируем пути к данным
from source import MODEL_PATH, CORPUS_PATH, PACKAGE_DATA_DIR


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
    Генератор паролей на основе Марковских цепей с поддержкой сохранения/загрузки модели.
    """

    def __init__(self, corpus_file_path: str = str(CORPUS_PATH), chain_order: int = 2, force_rebuild: bool = False):
        self.corpus_file_path = Path(corpus_file_path)
        self.chain_order = chain_order
        self.model = defaultdict(list)
        self.start_states = []

        # --- ЛОГИКА ЗАГРУЗКИ / ПОСТРОЕНИЯ МОДЕЛИ ---
        if MODEL_PATH.exists() and not force_rebuild:
            self._load_model()
        else:
            self._build_model()
            self._save_model()

    def _load_model(self):
        """Загружает модель из файла .pkl."""
        print(f"Загрузка существующей модели из {MODEL_PATH}...")
        try:
            with open(MODEL_PATH, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.start_states = data['start_states']
            print("Модель успешно загружена.")
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            print(f"Не удалось загрузить модель: {e}. Будет построена новая.")
            self._build_model()
            self._save_model()

    def _save_model(self):
        """Сохраняет модель в файл .pkl."""
        print(f"Сохранение модели в {MODEL_PATH}...")
        data_to_save = {
            'model': self.model,
            'start_states': self.start_states
        }
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(data_to_save, f)
        print("Модель успешно сохранена.")

    @staticmethod
    @lru_cache(maxsize=8)
    def _preprocess_text(text: str) -> str:
        """
        Очищает текст, оставляя только буквы (кириллица и латиница).
        """
        cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]', '', text)
        return cleaned_text.lower()

    def _build_model(self):
        """Строит модель Марковской цепи из очищенного текста."""
        print(f"Построение модели из файла {self.corpus_file_path}...")

        if not self.corpus_file_path.exists():
            raise FileNotFoundError(f"Файл корпуса не найден: {self.corpus_file_path}. Поместите его в {PACKAGE_DATA_DIR} или укажите другой путь.")

        with open(self.corpus_file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        clean_text = self._preprocess_text(text)
        if not clean_text:
            raise ValueError("После очистки текста в корпусе не осталось символов.")

        N = self.chain_order
        for i in range(len(clean_text) - N):
            state = clean_text[i:i + N]
            next_char = clean_text[i + N]
            self.model[state].append(next_char)

        self.start_states = [
            clean_text[i:i + N]
            for i in range(len(clean_text) - N)
            if i == 0 or clean_text[i - 1] == ' '
        ]

        if not self.start_states:
            self.start_states = list(self.model.keys())

        print(f"Модель построена. {len(self.model)} уникальных состояний.")

    def generate(self, length: int = 12) -> str:
        """
        Генерирует словоподобный пароль.
        """
        if not self.model:
            return "Ошибка: Модель не построена."

        start_state = random.choice(self.start_states)
        password_base = start_state

        while len(password_base) < length:
            state = password_base[-self.chain_order:]
            next_chars = self.model.get(state)

            if not next_chars:
                state = random.choice(list(self.model.keys()))
                next_chars = self.model[state]

            password_base += random.choice(next_chars)

        final_password = random_capitalize(password_base[:length])
        return final_password