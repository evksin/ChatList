"""
Модуль для работы с базой данных SQLite.
Инкапсулирует все операции с БД для приложения ChatList.
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class Database:
    """Класс для работы с базой данных SQLite."""
    
    def __init__(self, db_path: str = "chatlist.db"):
        """
        Инициализация подключения к базе данных.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_db()
    
    def _connect(self):
        """Установка соединения с базой данных."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _initialize_db(self):
        """Инициализация базы данных - создание таблиц и индексов."""
        cursor = self.conn.cursor()
        
        # Таблица prompts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                prompt TEXT NOT NULL,
                tags TEXT
            )
        """)
        
        # Таблица models
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_id TEXT NOT NULL,
                model_name TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        # Добавляем колонку model_name, если её нет (для существующих БД)
        try:
            cursor.execute("ALTER TABLE models ADD COLUMN model_name TEXT")
        except sqlite3.OperationalError:
            # Колонка уже существует, игнорируем ошибку
            pass
        
        # Таблица results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                selected INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
            )
        """)
        
        # Таблица settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY NOT NULL UNIQUE,
                value TEXT NOT NULL
            )
        """)
        
        # Индексы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_date ON results(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_selected ON results(selected)")
        
        # Инициализация настроек по умолчанию
        self._init_default_settings()
        
        self.conn.commit()
    
    def _init_default_settings(self):
        """Инициализация настроек по умолчанию."""
        default_settings = {
            'default_timeout': '30',
            'max_response_length': '10000',
            'auto_save': 'false',
            'theme': 'light',
            'font_size': '10',
            'export_format': 'markdown',
            'prompt_improver_enabled': 'true',
            'prompt_improver_model': ''  # Пустое значение - модель не выбрана
        }
        
        cursor = self.conn.cursor()
        for key, value in default_settings.items():
            cursor.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)
            """, (key, value))
    
    # ========== CRUD операции для prompts ==========
    
    def create_prompt(self, prompt: str, tags: Optional[str] = None) -> int:
        """Создать новый промт."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO prompts (prompt, tags) VALUES (?, ?)
        """, (prompt, tags))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict]:
        """Получить промт по ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_prompts(self, sort_by: str = 'date', order: str = 'DESC') -> List[Dict]:
        """Получить все промты с сортировкой."""
        valid_sort = ['id', 'date', 'prompt']
        valid_order = ['ASC', 'DESC']
        sort_by = sort_by if sort_by in valid_sort else 'date'
        order = order if order in valid_order else 'DESC'
        
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM prompts ORDER BY {sort_by} {order}")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_prompt(self, prompt_id: int, prompt: Optional[str] = None, 
                     tags: Optional[str] = None) -> bool:
        """Обновить промт."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if prompt is not None:
            updates.append("prompt = ?")
            params.append(prompt)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        
        if not updates:
            return False
        
        params.append(prompt_id)
        cursor.execute(f"""
            UPDATE prompts SET {', '.join(updates)} WHERE id = ?
        """, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """Удалить промт."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def search_prompts(self, query: str) -> List[Dict]:
        """Поиск промтов по тексту или тегам."""
        cursor = self.conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM prompts 
            WHERE prompt LIKE ? OR tags LIKE ?
            ORDER BY date DESC
        """, (search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== CRUD операции для models ==========
    
    def create_model(self, name: str, api_url: str, api_id: str, 
                    model_name: Optional[str] = None, is_active: int = 1) -> int:
        """Создать новую модель."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO models (name, api_url, api_id, model_name, is_active) 
            VALUES (?, ?, ?, ?, ?)
        """, (name, api_url, api_id, model_name, is_active))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_model(self, model_id: int) -> Optional[Dict]:
        """Получить модель по ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_all_models(self) -> List[Dict]:
        """Получить все модели."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM models ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_models(self) -> List[Dict]:
        """Получить все активные модели."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_model(self, model_id: int, name: Optional[str] = None,
                    api_url: Optional[str] = None, api_id: Optional[str] = None,
                    model_name: Optional[str] = None, is_active: Optional[int] = None) -> bool:
        """Обновить модель."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if api_url is not None:
            updates.append("api_url = ?")
            params.append(api_url)
        if api_id is not None:
            updates.append("api_id = ?")
            params.append(api_id)
        if model_name is not None:
            updates.append("model_name = ?")
            params.append(model_name)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            return False
        
        params.append(model_id)
        cursor.execute(f"""
            UPDATE models SET {', '.join(updates)} WHERE id = ?
        """, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_model(self, model_id: int) -> bool:
        """Удалить модель."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ========== CRUD операции для results ==========
    
    def create_result(self, prompt_id: int, model_id: int, response: str, 
                     selected: int = 0) -> int:
        """Создать новый результат."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO results (prompt_id, model_id, response, selected) 
            VALUES (?, ?, ?, ?)
        """, (prompt_id, model_id, response, selected))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_result(self, result_id: int) -> Optional[Dict]:
        """Получить результат по ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM results WHERE id = ?", (result_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_results_by_prompt(self, prompt_id: int) -> List[Dict]:
        """Получить все результаты для конкретного промта."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, m.name as model_name 
            FROM results r
            JOIN models m ON r.model_id = m.id
            WHERE r.prompt_id = ?
            ORDER BY r.date DESC
        """, (prompt_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_selected_results(self) -> List[Dict]:
        """Получить все выбранные результаты."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT r.*, m.name as model_name, p.prompt as prompt_text
            FROM results r
            JOIN models m ON r.model_id = m.id
            JOIN prompts p ON r.prompt_id = p.id
            WHERE r.selected = 1
            ORDER BY r.date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def update_result(self, result_id: int, response: Optional[str] = None,
                     selected: Optional[int] = None) -> bool:
        """Обновить результат."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if response is not None:
            updates.append("response = ?")
            params.append(response)
        if selected is not None:
            updates.append("selected = ?")
            params.append(selected)
        
        if not updates:
            return False
        
        params.append(result_id)
        cursor.execute(f"""
            UPDATE results SET {', '.join(updates)} WHERE id = ?
        """, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_result(self, result_id: int) -> bool:
        """Удалить результат."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def search_results(self, query: str) -> List[Dict]:
        """Поиск результатов по тексту ответа."""
        cursor = self.conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT r.*, m.name as model_name, p.prompt as prompt_text
            FROM results r
            JOIN models m ON r.model_id = m.id
            JOIN prompts p ON r.prompt_id = p.id
            WHERE r.response LIKE ?
            ORDER BY r.date DESC
        """, (search_term,))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== Операции для settings ==========
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Получить значение настройки."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """Установить значение настройки."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self.conn.commit()
        return True
    
    def get_all_settings(self) -> Dict[str, str]:
        """Получить все настройки."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row['key']: row['value'] for row in cursor.fetchall()}
    
    def close(self):
        """Закрыть соединение с базой данных."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Контекстный менеджер - вход."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        self.close()


# Глобальный экземпляр базы данных
_db_instance = None


def get_db(db_path: str = "chatlist.db") -> Database:
    """Получить экземпляр базы данных (singleton)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance

