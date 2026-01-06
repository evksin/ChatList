"""
Основной модуль приложения ChatList.
Реализует графический интерфейс для работы с нейросетевыми моделями.
"""

import sys
from typing import List, Dict, Optional
import markdown
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
    QCheckBox, QComboBox, QMenuBar, QMenu, QStatusBar, QMessageBox,
    QDialog, QLineEdit, QDialogButtonBox, QGroupBox, QProgressBar,
    QHeaderView, QSplitter, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
from db import get_db
from models import get_model_manager


class RequestThread(QThread):
    """Поток для асинхронной отправки запросов к API."""
    
    finished = pyqtSignal(list)  # Сигнал с результатами
    
    def __init__(self, prompt: str, model_manager):
        super().__init__()
        self.prompt = prompt
        self.model_manager = model_manager
    
    def run(self):
        """Выполнить запросы к API."""
        results = self.model_manager.send_prompt_to_all_active(self.prompt)
        self.finished.emit(results)


class ModelDialog(QDialog):
    """Диалог для добавления/редактирования модели."""
    
    def __init__(self, parent=None, model_data: Optional[Dict] = None):
        super().__init__(parent)
        self.model_data = model_data
        self.setWindowTitle("Редактировать модель" if model_data else "Добавить модель")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Название модели
        layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        if self.model_data:
            self.name_edit.setText(self.model_data.get('name', ''))
        layout.addWidget(self.name_edit)
        
        # API URL
        layout.addWidget(QLabel("API URL:"))
        self.url_edit = QLineEdit()
        if self.model_data:
            self.url_edit.setText(self.model_data.get('api_url', ''))
        layout.addWidget(self.url_edit)
        
        # API ID (имя переменной окружения)
        layout.addWidget(QLabel("API ID (имя переменной в .env):"))
        self.api_id_edit = QLineEdit()
        if self.model_data:
            self.api_id_edit.setText(self.model_data.get('api_id', ''))
        layout.addWidget(self.api_id_edit)
        
        # Model Name (имя модели для API, например, anthropic/claude-3-haiku)
        layout.addWidget(QLabel("Model Name (имя модели для API, опционально):"))
        self.model_name_edit = QLineEdit()
        if self.model_data:
            self.model_name_edit.setText(self.model_data.get('model_name', ''))
        layout.addWidget(self.model_name_edit)
        
        # Активна ли модель
        self.active_checkbox = QCheckBox("Активна")
        if self.model_data:
            self.active_checkbox.setChecked(bool(self.model_data.get('is_active', 1)))
        else:
            self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Получить данные модели из формы."""
        return {
            'name': self.name_edit.text(),
            'api_url': self.url_edit.text(),
            'api_id': self.api_id_edit.text(),
            'model_name': self.model_name_edit.text().strip() or None,
            'is_active': 1 if self.active_checkbox.isChecked() else 0
        }


class PromptImprovementDialog(QDialog):
    """Диалог для отображения улучшенных промтов."""
    
    def __init__(self, parent=None, original_prompt: str = "", improvement_result: Dict = None):
        super().__init__(parent)
        self.setWindowTitle("Улучшенные варианты промта")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Исходный промт
        original_group = QGroupBox("Исходный промт")
        original_layout = QVBoxLayout()
        original_text = QTextEdit()
        original_text.setReadOnly(True)
        original_text.setPlainText(original_prompt)
        original_text.setMaximumHeight(80)
        original_layout.addWidget(original_text)
        original_group.setLayout(original_layout)
        layout.addWidget(original_group)
        
        # Улучшенная версия
        improved_group = QGroupBox("Улучшенная версия")
        improved_layout = QVBoxLayout()
        self.improved_text = QTextEdit()
        self.improved_text.setReadOnly(True)
        self.improved_text.setPlainText(improvement_result.get('improved', ''))
        self.improved_text.setMaximumHeight(100)
        improved_layout.addWidget(self.improved_text)
        
        improved_buttons = QHBoxLayout()
        use_improved_btn = QPushButton("Использовать этот вариант")
        use_improved_btn.clicked.connect(lambda: self.use_prompt(improvement_result.get('improved', '')))
        improved_buttons.addWidget(use_improved_btn)
        
        copy_improved_btn = QPushButton("Копировать")
        copy_improved_btn.clicked.connect(lambda: self.copy_to_clipboard(improvement_result.get('improved', '')))
        improved_buttons.addWidget(copy_improved_btn)
        improved_layout.addLayout(improved_buttons)
        improved_group.setLayout(improved_layout)
        layout.addWidget(improved_group)
        
        # Альтернативные варианты
        alternatives_group = QGroupBox("Альтернативные варианты")
        alternatives_layout = QVBoxLayout()
        
        alternatives = improvement_result.get('alternatives', [])
        self.alternative_widgets = []
        
        for i, alt in enumerate(alternatives):
            alt_layout = QHBoxLayout()
            alt_text = QTextEdit()
            alt_text.setReadOnly(True)
            alt_text.setPlainText(alt)
            alt_text.setMaximumHeight(60)
            alt_layout.addWidget(alt_text)
            
            alt_buttons = QHBoxLayout()
            use_alt_btn = QPushButton(f"Использовать вариант {i+1}")
            use_alt_btn.clicked.connect(lambda checked, text=alt: self.use_prompt(text))
            alt_buttons.addWidget(use_alt_btn)
            
            copy_alt_btn = QPushButton("Копировать")
            copy_alt_btn.clicked.connect(lambda checked, text=alt: self.copy_to_clipboard(text))
            alt_buttons.addWidget(copy_alt_btn)
            alt_layout.addLayout(alt_buttons)
            alternatives_layout.addLayout(alt_layout)
            self.alternative_widgets.append(alt_text)
        
        if not alternatives:
            no_alternatives_label = QLabel("Альтернативные варианты не предоставлены")
            alternatives_layout.addWidget(no_alternatives_label)
        
        alternatives_group.setLayout(alternatives_layout)
        layout.addWidget(alternatives_group)
        
        # Адаптированные версии
        adaptations = improvement_result.get('adaptations', {})
        if adaptations:
            adaptations_group = QGroupBox("Адаптированные версии")
            adaptations_layout = QVBoxLayout()
            
            if 'code' in adaptations:
                code_layout = QHBoxLayout()
                code_text = QTextEdit()
                code_text.setReadOnly(True)
                code_text.setPlainText(adaptations['code'])
                code_text.setMaximumHeight(60)
                code_layout.addWidget(QLabel("Для программирования:"))
                code_layout.addWidget(code_text)
                code_buttons = QHBoxLayout()
                use_code_btn = QPushButton("Использовать")
                use_code_btn.clicked.connect(lambda: self.use_prompt(adaptations['code']))
                code_buttons.addWidget(use_code_btn)
                copy_code_btn = QPushButton("Копировать")
                copy_code_btn.clicked.connect(lambda: self.copy_to_clipboard(adaptations['code']))
                code_buttons.addWidget(copy_code_btn)
                code_layout.addLayout(code_buttons)
                adaptations_layout.addLayout(code_layout)
            
            if 'analysis' in adaptations:
                analysis_layout = QHBoxLayout()
                analysis_text = QTextEdit()
                analysis_text.setReadOnly(True)
                analysis_text.setPlainText(adaptations['analysis'])
                analysis_text.setMaximumHeight(60)
                analysis_layout.addWidget(QLabel("Для анализа:"))
                analysis_layout.addWidget(analysis_text)
                analysis_buttons_layout = QHBoxLayout()
                use_analysis_btn = QPushButton("Использовать")
                use_analysis_btn.clicked.connect(lambda: self.use_prompt(adaptations['analysis']))
                analysis_buttons_layout.addWidget(use_analysis_btn)
                
                copy_analysis_btn = QPushButton("Копировать")
                copy_analysis_btn.clicked.connect(lambda: self.copy_to_clipboard(adaptations['analysis']))
                analysis_buttons_layout.addWidget(copy_analysis_btn)
                analysis_layout.addLayout(analysis_buttons_layout)
                adaptations_layout.addLayout(analysis_layout)
            
            if 'creative' in adaptations:
                creative_layout = QHBoxLayout()
                creative_text = QTextEdit()
                creative_text.setReadOnly(True)
                creative_text.setPlainText(adaptations['creative'])
                creative_text.setMaximumHeight(60)
                creative_layout.addWidget(QLabel("Для креатива:"))
                creative_layout.addWidget(creative_text)
                creative_buttons_layout = QHBoxLayout()
                use_creative_btn = QPushButton("Использовать")
                use_creative_btn.clicked.connect(lambda: self.use_prompt(adaptations['creative']))
                creative_buttons_layout.addWidget(use_creative_btn)
                
                copy_creative_btn = QPushButton("Копировать")
                copy_creative_btn.clicked.connect(lambda: self.copy_to_clipboard(adaptations['creative']))
                creative_buttons_layout.addWidget(copy_creative_btn)
                creative_layout.addLayout(creative_buttons_layout)
                adaptations_layout.addLayout(creative_layout)
            
            adaptations_group.setLayout(adaptations_layout)
            layout.addWidget(adaptations_group)
        
        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self.selected_prompt = None
    
    def use_prompt(self, prompt_text: str):
        """Использовать выбранный промт."""
        self.selected_prompt = prompt_text
        self.accept()
    
    def get_selected_prompt(self) -> Optional[str]:
        """Получить выбранный промт."""
        return self.selected_prompt
    
    def copy_to_clipboard(self, text: str):
        """Копировать текст в буфер обмена."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Скопировано", "Текст скопирован в буфер обмена!")


class PromptDialog(QDialog):
    """Диалог для добавления/редактирования промта."""
    
    def __init__(self, parent=None, prompt_data: Optional[Dict] = None):
        super().__init__(parent)
        self.prompt_data = prompt_data
        self.setWindowTitle("Редактировать промт" if prompt_data else "Добавить промт")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Текст промта
        layout.addWidget(QLabel("Промт:"))
        self.prompt_edit = QTextEdit()
        if self.prompt_data:
            self.prompt_edit.setPlainText(self.prompt_data.get('prompt', ''))
        layout.addWidget(self.prompt_edit)
        
        # Теги
        layout.addWidget(QLabel("Теги (через запятую):"))
        self.tags_edit = QLineEdit()
        if self.prompt_data:
            self.tags_edit.setText(self.prompt_data.get('tags', ''))
        layout.addWidget(self.tags_edit)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def get_data(self) -> Dict:
        """Получить данные промта из формы."""
        return {
            'prompt': self.prompt_edit.toPlainText(),
            'tags': self.tags_edit.text()
        }


class MainWindow(QMainWindow):
    """Главное окно приложения ChatList."""
    
    def __init__(self):
        super().__init__()
        self.db = get_db()
        self.model_manager = get_model_manager()
        self.temp_results = []  # Временная таблица результатов в памяти
        self.request_thread = None
        
        self.setWindowTitle("ChatList - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1200, 800)
        
        # Устанавливаем иконку приложения
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "app.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Применяем сохранённые настройки
        self.load_settings()
        
        self.init_ui()
        self.load_saved_prompts()
        self.load_models()
    
    def load_settings(self):
        """Загрузить и применить сохранённые настройки."""
        theme = self.db.get_setting('theme', 'light')
        self.apply_theme(theme)
        
        font_size = int(self.db.get_setting('font_size', '10'))
        self.apply_font_size(font_size)
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Создаём меню
        self.create_menu()
        
        # Группа ввода промта
        prompt_group = QGroupBox("Ввод промта")
        prompt_layout = QVBoxLayout()
        
        # Выбор сохранённого промта
        prompt_select_layout = QHBoxLayout()
        prompt_select_layout.addWidget(QLabel("Выбрать сохранённый промт:"))
        self.prompt_combo = QComboBox()
        self.prompt_combo.currentTextChanged.connect(self.on_prompt_selected)
        prompt_select_layout.addWidget(self.prompt_combo)
        prompt_layout.addLayout(prompt_select_layout)
        
        # Поле ввода нового промта
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Введите ваш промт здесь...")
        self.prompt_edit.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_edit)
        
        # Кнопки действий с промтом
        buttons_layout = QHBoxLayout()
        self.improve_button = QPushButton("Улучшить промт")
        self.improve_button.clicked.connect(self.improve_prompt)
        buttons_layout.addWidget(self.improve_button)
        
        buttons_layout.addStretch()
        
        self.send_button = QPushButton("Отправить запрос")
        self.send_button.clicked.connect(self.send_request)
        buttons_layout.addWidget(self.send_button)
        prompt_layout.addLayout(buttons_layout)
        
        prompt_group.setLayout(prompt_layout)
        main_layout.addWidget(prompt_group)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Разделитель для таблицы результатов
        splitter = QSplitter(Qt.Vertical)
        
        # Таблица результатов
        results_group = QGroupBox("Результаты")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Модель", "Ответ", "Открыть", "Выбрать"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.results_table.setAlternatingRowColors(True)
        
        # Устанавливаем минимальную высоту строк для многострочного отображения
        self.results_table.verticalHeader().setDefaultSectionSize(100)
        self.results_table.verticalHeader().setMinimumSectionSize(60)
        
        # Включаем перенос текста для ячеек (работает с QTableWidgetItem)
        # Перенос текста будет работать автоматически благодаря setWordWrap
        
        results_layout.addWidget(self.results_table)
        
        # Кнопка сохранения
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_button = QPushButton("Сохранить выбранные результаты")
        self.save_button.clicked.connect(self.save_selected_results)
        self.save_button.setEnabled(False)
        save_layout.addWidget(self.save_button)
        results_layout.addLayout(save_layout)
        
        results_group.setLayout(results_layout)
        splitter.addWidget(results_group)
        main_layout.addWidget(splitter)
        
        # Статус-бар
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готово")
    
    def create_menu(self):
        """Создание меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Модели"
        models_menu = menubar.addMenu("Модели")
        models_menu.addAction("Управление моделями", self.manage_models)
        
        # Меню "Промты"
        prompts_menu = menubar.addMenu("Промты")
        prompts_menu.addAction("Управление промтами", self.manage_prompts)
        
        # Меню "Результаты"
        results_menu = menubar.addMenu("Результаты")
        results_menu.addAction("Просмотр сохранённых", self.view_saved_results)
        results_menu.addAction("Экспорт в Markdown", lambda: self.export_results('markdown'))
        results_menu.addAction("Экспорт в JSON", lambda: self.export_results('json'))
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        settings_menu.addAction("Настройки программы", self.show_settings)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        help_menu.addAction("О программе", self.show_about)
    
    def load_saved_prompts(self):
        """Загрузить сохранённые промты в выпадающий список."""
        self.prompt_combo.clear()
        self.prompt_combo.addItem("-- Новый промт --")
        
        prompts = self.db.get_all_prompts()
        for prompt in prompts:
            preview = prompt['prompt'][:50] + "..." if len(prompt['prompt']) > 50 else prompt['prompt']
            self.prompt_combo.addItem(f"{prompt['id']}: {preview}", prompt)
    
    def load_models(self):
        """Загрузить список моделей (для отображения в статусе)."""
        models = self.db.get_all_models()
        active_count = sum(1 for m in models if m['is_active'])
        self.statusBar.showMessage(f"Моделей: {len(models)} (активных: {active_count})")
    
    def on_prompt_selected(self, text):
        """Обработчик выбора промта из списка."""
        if text == "-- Новый промт --":
            self.prompt_edit.clear()
            return
        
        index = self.prompt_combo.currentIndex()
        if index > 0:
            prompt_data = self.prompt_combo.itemData(index)
            if prompt_data:
                self.prompt_edit.setPlainText(prompt_data['prompt'])
    
    def send_request(self):
        """Отправить запрос ко всем активным моделям."""
        prompt_text = self.prompt_edit.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Предупреждение", "Введите промт перед отправкой!")
            return
        
        active_models = self.db.get_active_models()
        if not active_models:
            QMessageBox.warning(self, "Предупреждение", "Нет активных моделей! Добавьте модели в меню 'Модели'.")
            return
        
        # Очищаем временную таблицу
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.save_button.setEnabled(False)
        
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределённый прогресс
        self.send_button.setEnabled(False)
        self.statusBar.showMessage("Отправка запросов...")
        
        # Запускаем запросы в отдельном потоке
        self.request_thread = RequestThread(prompt_text, self.model_manager)
        self.request_thread.finished.connect(self.on_requests_finished)
        self.request_thread.start()
    
    def on_requests_finished(self, results: List[Dict]):
        """Обработчик завершения запросов."""
        self.progress_bar.setVisible(False)
        self.send_button.setEnabled(True)
        
        # Сохраняем результаты во временную таблицу
        self.temp_results = results
        
        # Отображаем результаты
        self.results_table.setRowCount(len(results))
        
        success_count = 0
        error_count = 0
        
        for row, result in enumerate(results):
            # Модель
            model_name = result.get('model_name', 'Unknown')
            model_item = QTableWidgetItem(model_name)
            
            # Окрашиваем строку в зависимости от результата
            if not result.get('success', False):
                model_item.setForeground(Qt.red)
                error_count += 1
            else:
                success_count += 1
            
            self.results_table.setItem(row, 0, model_item)
            
            # Ответ - используем QTableWidgetItem с переносом текста
            if result.get('success', False):
                response_text = result.get('text', '')
            else:
                error_msg = result.get('error', 'Ошибка получения ответа')
                response_text = f"ОШИБКА: {error_msg}"
            
            response_item = QTableWidgetItem(response_text)
            # Включаем перенос текста
            response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            
            # Устанавливаем цвет текста для ошибок
            if not result.get('success', False):
                response_item.setForeground(Qt.red)
            
            self.results_table.setItem(row, 1, response_item)
            
            # Автоматически подстраиваем высоту строки под содержимое
            # Подсчитываем примерное количество строк
            lines = len(response_text.split('\n'))
            # Учитываем переносы по ширине (примерно 80 символов на строку)
            char_lines = len(response_text) // 80
            total_lines = max(lines, char_lines, 3)  # Минимум 3 строки
            
            # Устанавливаем высоту строки (примерно 25 пикселей на строку)
            row_height = min(total_lines * 25 + 10, 400)  # Максимум 400px
            self.results_table.setRowHeight(row, row_height)
            
            # Кнопка "Открыть" (только для успешных ответов)
            open_button = QPushButton("Открыть")
            open_button.setEnabled(result.get('success', False))  # Отключаем для ошибок
            if result.get('success', False):
                open_button.clicked.connect(lambda checked, r=row: self.open_response_dialog(r))
            else:
                open_button.setToolTip("Невозможно открыть ответ с ошибкой")
            self.results_table.setCellWidget(row, 2, open_button)
            
            # Чекбокс (только для успешных ответов)
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            checkbox.setEnabled(result.get('success', False))  # Отключаем для ошибок
            checkbox.stateChanged.connect(self.on_checkbox_changed)
            self.results_table.setCellWidget(row, 3, checkbox)
        
        # Сохраняем промт в БД, если его там ещё нет
        prompt_text = self.prompt_edit.toPlainText().strip()
        self.db.create_prompt(prompt_text)
        self.load_saved_prompts()
        
        self.save_button.setEnabled(True)
        
        # Показываем статистику
        status_msg = f"Успешно: {success_count}, Ошибок: {error_count}"
        if error_count > 0:
            QMessageBox.warning(
                self, "Предупреждение",
                f"Некоторые запросы завершились с ошибками.\n\n{status_msg}\n\nПроверьте логи в папке logs/ для подробностей."
            )
        self.statusBar.showMessage(status_msg)
    
    def on_checkbox_changed(self):
        """Обработчик изменения чекбоксов."""
        # Можно добавить логику, если нужно
        pass
    
    def improve_prompt(self):
        """Улучшить промт с помощью AI."""
        from prompt_improver import PromptImprover
        
        prompt_text = self.prompt_edit.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Предупреждение", "Введите промт для улучшения!")
            return
        
        # Создаём улучшатель промтов
        improver = PromptImprover(self.db, self.model_manager)
        
        # Проверяем, включена ли функция
        if not improver.is_enabled():
            reply = QMessageBox.question(
                self, "Функция отключена",
                "Функция улучшения промтов отключена в настройках.\n\nХотите открыть настройки?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.show_settings()
            return
        
        # Проверяем, выбрана ли модель
        if not improver.get_improver_model_id():
            reply = QMessageBox.question(
                self, "Модель не выбрана",
                "Модель для улучшения промтов не выбрана в настройках.\n\nХотите открыть настройки?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.show_settings()
            return
        
        # Показываем прогресс
        self.statusBar.showMessage("Улучшение промта...")
        self.improve_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Неопределённый прогресс
        
        try:
            # Улучшаем промт
            result = improver.improve_prompt(prompt_text)
            
            if not result.get('success', False):
                error_msg = result.get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка улучшения промта", error_msg)
                self.statusBar.showMessage("Ошибка улучшения промта")
                return
            
            # Показываем диалог с результатами
            dialog = PromptImprovementDialog(self, prompt_text, result)
            if dialog.exec_() == QDialog.Accepted:
                selected = dialog.get_selected_prompt()
                if selected:
                    self.prompt_edit.setPlainText(selected)
                    self.statusBar.showMessage("Промт обновлён")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при улучшении промта:\n{str(e)}")
            self.statusBar.showMessage("Ошибка улучшения промта")
        finally:
            self.progress_bar.setVisible(False)
            self.improve_button.setEnabled(True)
            self.statusBar.showMessage("Готово")
    
    def open_response_dialog(self, row: int):
        """Открыть диалог с форматированным markdown ответом."""
        if row < 0 or row >= len(self.temp_results):
            return
        
        result = self.temp_results[row]
        if not result.get('success', False):
            QMessageBox.warning(self, "Предупреждение", "Невозможно открыть ответ с ошибкой!")
            return
        
        response_text = result.get('text', '')
        model_name = result.get('model_name', 'Unknown')
        
        # Создаём диалог
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ответ модели: {model_name}")
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Заголовок с названием модели
        header_label = QLabel(f"<h2>Ответ модели: {model_name}</h2>")
        layout.addWidget(header_label)
        
        # Текстовое поле для отображения markdown
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # Конвертируем markdown в HTML
        try:
            html_content = markdown.markdown(
                response_text,
                extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
            )
            # Добавляем базовые стили для лучшего отображения
            styled_html = f"""
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333;
                    padding: 10px;
                }}
                pre {{
                    background-color: #f4f4f4;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    overflow-x: auto;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                ul, ol {{
                    margin-left: 20px;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    margin-left: 0;
                    padding-left: 20px;
                    color: #666;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
            <body>
            {html_content}
            </body>
            """
            text_edit.setHtml(styled_html)
        except Exception as e:
            # Если не удалось конвертировать markdown, показываем как обычный текст
            text_edit.setPlainText(response_text)
            QMessageBox.warning(self, "Предупреждение", f"Ошибка форматирования markdown: {str(e)}")
        
        layout.addWidget(text_edit)
        
        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def save_selected_results(self):
        """Сохранить выбранные результаты в БД."""
        if not self.temp_results:
            QMessageBox.warning(self, "Предупреждение", "Нет результатов для сохранения!")
            return
        
        # Получаем текст промта
        prompt_text = self.prompt_edit.toPlainText().strip()
        
        # Создаём или находим промт в БД
        prompts = self.db.search_prompts(prompt_text)
        if prompts and prompts[0]['prompt'] == prompt_text:
            prompt_id = prompts[0]['id']
        else:
            prompt_id = self.db.create_prompt(prompt_text)
        
        # Сохраняем выбранные результаты
        saved_count = 0
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 3)
            if checkbox and checkbox.isChecked():
                result = self.temp_results[row]
                model_id = result.get('model_id')
                response_text = result.get('text', '')
                
                if model_id and response_text:
                    self.db.create_result(prompt_id, model_id, response_text, selected=1)
                    saved_count += 1
        
        if saved_count > 0:
            QMessageBox.information(self, "Успех", f"Сохранено результатов: {saved_count}")
            self.statusBar.showMessage(f"Сохранено результатов: {saved_count}")
        else:
            QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одного результата!")
    
    def manage_models(self):
        """Управление моделями."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление моделями")
        dialog.setModal(True)
        dialog.resize(900, 600)
        layout = QVBoxLayout()
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Введите название модели для поиска...")
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # Таблица моделей
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Название", "API URL", "API ID", "Активна"])
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        
        def filter_table(text):
            """Фильтрация таблицы по поисковому запросу."""
            for row in range(table.rowCount()):
                item = table.item(row, 1)  # Поиск по названию
                if item:
                    match = text.lower() in item.text().lower()
                    table.setRowHidden(row, not match)
        
        search_input.textChanged.connect(filter_table)
        
        models = self.db.get_all_models()
        table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            table.setItem(row, 0, QTableWidgetItem(str(model['id'])))
            table.setItem(row, 1, QTableWidgetItem(model['name']))
            table.setItem(row, 2, QTableWidgetItem(model['api_url']))
            table.setItem(row, 3, QTableWidgetItem(model['api_id']))
            checkbox = QCheckBox()
            checkbox.setChecked(bool(model['is_active']))
            table.setCellWidget(row, 4, checkbox)
        
        layout.addWidget(table)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(lambda: self.add_model(dialog))
        buttons_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda: self.edit_model(table, dialog))
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(lambda: self.delete_model(table, dialog))
        buttons_layout.addWidget(delete_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        self.load_models()
    
    def add_model(self, parent_dialog):
        """Добавить новую модель."""
        dialog = ModelDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.create_model(**data)
            parent_dialog.accept()
            self.manage_models()
    
    def edit_model(self, table, parent_dialog):
        """Редактировать модель."""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для редактирования!")
            return
        
        model_id = int(table.item(current_row, 0).text())
        model_data = self.db.get_model(model_id)
        
        dialog = ModelDialog(self, model_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.update_model(model_id, **data)
            parent_dialog.accept()
            self.manage_models()
    
    def delete_model(self, table, parent_dialog):
        """Удалить модель."""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите модель для удаления!")
            return
        
        model_id = int(table.item(current_row, 0).text())
        model_name = table.item(current_row, 1).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить модель '{model_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_model(model_id)
            parent_dialog.accept()
            self.manage_models()
    
    def manage_prompts(self):
        """Управление промтами."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Управление промтами")
        dialog.setModal(True)
        dialog.resize(900, 600)
        layout = QVBoxLayout()
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Введите текст для поиска по промтам или тегам...")
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # Таблица промтов
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["ID", "Дата", "Промт", "Теги", "Действия"])
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        
        def filter_table(text):
            """Фильтрация таблицы по поисковому запросу."""
            for row in range(table.rowCount()):
                prompt_item = table.item(row, 2)
                tags_item = table.item(row, 3)
                match = False
                if prompt_item and text.lower() in prompt_item.text().lower():
                    match = True
                if tags_item and text.lower() in tags_item.text().lower():
                    match = True
                table.setRowHidden(row, not match)
        
        search_input.textChanged.connect(filter_table)
        
        prompts = self.db.get_all_prompts()
        table.setRowCount(len(prompts))
        
        for row, prompt in enumerate(prompts):
            table.setItem(row, 0, QTableWidgetItem(str(prompt['id'])))
            table.setItem(row, 1, QTableWidgetItem(prompt['date']))
            table.setItem(row, 2, QTableWidgetItem(prompt['prompt']))
            table.setItem(row, 3, QTableWidgetItem(prompt.get('tags', '')))
            
            # Кнопки действий для каждой строки
            actions_layout = QHBoxLayout()
            actions_widget = QWidget()
            
            edit_btn = QPushButton("Изменить")
            edit_btn.setMaximumWidth(80)
            edit_btn.clicked.connect(lambda checked, r=row, p_id=prompt['id']: self.edit_prompt_row(table, dialog, r, p_id))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("Удалить")
            delete_btn.setMaximumWidth(80)
            delete_btn.clicked.connect(lambda checked, r=row, p_id=prompt['id']: self.delete_prompt_row(table, dialog, r, p_id))
            actions_layout.addWidget(delete_btn)
            
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            actions_widget.setLayout(actions_layout)
            table.setCellWidget(row, 4, actions_widget)
        
        layout.addWidget(table)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить новый промт")
        add_btn.clicked.connect(lambda: self.add_prompt(dialog))
        buttons_layout.addWidget(add_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        dialog.setLayout(layout)
        dialog.exec_()
        self.load_saved_prompts()
    
    def add_prompt(self, parent_dialog):
        """Добавить новый промт."""
        dialog = PromptDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.create_prompt(data['prompt'], data.get('tags'))
            parent_dialog.accept()
            self.manage_prompts()
    
    def edit_prompt(self, table, parent_dialog):
        """Редактировать промт (старый метод для совместимости)."""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите промт для редактирования!")
            return
        
        prompt_id = int(table.item(current_row, 0).text())
        self.edit_prompt_row(table, parent_dialog, current_row, prompt_id)
    
    def edit_prompt_row(self, table, parent_dialog, row, prompt_id):
        """Редактировать промт по строке и ID."""
        prompt_data = self.db.get_prompt(prompt_id)
        
        dialog = PromptDialog(self, prompt_data)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.db.update_prompt(prompt_id, data['prompt'], data.get('tags'))
            parent_dialog.accept()
            self.manage_prompts()
    
    def delete_prompt(self, table, parent_dialog):
        """Удалить промт (старый метод для совместимости)."""
        current_row = table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите промт для удаления!")
            return
        
        prompt_id = int(table.item(current_row, 0).text())
        self.delete_prompt_row(table, parent_dialog, current_row, prompt_id)
    
    def delete_prompt_row(self, table, parent_dialog, row, prompt_id):
        """Удалить промт по строке и ID."""
        prompt_text = table.item(row, 2).text() if table.item(row, 2) else ""
        preview = prompt_text[:50] + "..." if len(prompt_text) > 50 else prompt_text
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить промт '{preview}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.delete_prompt(prompt_id)
            parent_dialog.accept()
            self.manage_prompts()
    
    def view_saved_results(self):
        """Просмотр сохранённых результатов."""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Сохранённые результаты")
        dialog.setModal(True)
        dialog.resize(1200, 700)
        layout = QVBoxLayout()
        
        # Поиск
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Введите текст для поиска по промтам, моделям или ответам...")
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)
        
        # Таблица результатов
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Дата", "Промт", "Модель", "Ответ"])
        table.setSortingEnabled(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        
        def filter_table(text):
            """Фильтрация таблицы по поисковому запросу."""
            for row in range(table.rowCount()):
                prompt_item = table.item(row, 1)
                model_item = table.item(row, 2)
                response_item = table.item(row, 3)
                match = False
                if prompt_item and text.lower() in prompt_item.text().lower():
                    match = True
                if model_item and text.lower() in model_item.text().lower():
                    match = True
                if response_item and text.lower() in response_item.text().lower():
                    match = True
                table.setRowHidden(row, not match)
        
        search_input.textChanged.connect(filter_table)
        
        results = self.db.get_selected_results()
        table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            table.setItem(row, 0, QTableWidgetItem(result.get('date', '')))
            table.setItem(row, 1, QTableWidgetItem(result.get('prompt_text', '')))
            table.setItem(row, 2, QTableWidgetItem(result.get('model_name', '')))
            table.setItem(row, 3, QTableWidgetItem(result.get('response', '')))
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def export_results(self, format_type: str):
        """Экспорт результатов."""
        results = self.db.get_selected_results()
        
        if not results:
            QMessageBox.warning(self, "Предупреждение", "Нет сохранённых результатов для экспорта!")
            return
        
        from PyQt5.QtWidgets import QFileDialog
        if format_type == 'markdown':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как Markdown", "", "Markdown (*.md)"
            )
            if filename:
                self.export_to_markdown(results, filename)
        elif format_type == 'json':
            filename, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как JSON", "", "JSON (*.json)"
            )
            if filename:
                self.export_to_json(results, filename)
    
    def export_to_markdown(self, results: List[Dict], filename: str):
        """Экспорт в Markdown."""
        import datetime
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Экспорт результатов ChatList\n\n")
            f.write(f"Дата экспорта: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for result in results:
                f.write(f"## {result.get('model_name', 'Unknown')}\n\n")
                f.write(f"**Промт:** {result.get('prompt_text', '')}\n\n")
                f.write(f"**Дата:** {result.get('date', '')}\n\n")
                f.write(f"**Ответ:**\n\n{result.get('response', '')}\n\n")
                f.write("---\n\n")
        
        QMessageBox.information(self, "Успех", f"Результаты экспортированы в {filename}")
    
    def export_to_json(self, results: List[Dict], filename: str):
        """Экспорт в JSON."""
        import json
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        QMessageBox.information(self, "Успех", f"Результаты экспортированы в {filename}")
    
    def show_settings(self):
        """Показать настройки программы."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки программы")
        dialog.setModal(True)
        dialog.resize(500, 500)
        layout = QVBoxLayout()
        
        # Группа настроек внешнего вида
        appearance_group = QGroupBox("Внешний вид")
        appearance_layout = QVBoxLayout()
        
        # Выбор темы
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Тема оформления:"))
        theme_combo = QComboBox()
        theme_combo.addItem("Светлая", "light")
        theme_combo.addItem("Тёмная", "dark")
        current_theme = self.db.get_setting('theme', 'light')
        theme_index = theme_combo.findData(current_theme)
        if theme_index >= 0:
            theme_combo.setCurrentIndex(theme_index)
        theme_layout.addWidget(theme_combo)
        appearance_layout.addLayout(theme_layout)
        
        # Выбор размера шрифта
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Размер шрифта:"))
        font_size_spinbox = QSpinBox()
        font_size_spinbox.setRange(8, 20)
        font_size_spinbox.setValue(int(self.db.get_setting('font_size', '10')))
        font_size_spinbox.setSuffix(" pt")
        font_size_layout.addWidget(font_size_spinbox)
        appearance_layout.addLayout(font_size_layout)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Группа настроек улучшения промтов
        improver_group = QGroupBox("AI-ассистент для улучшения промтов")
        improver_layout = QVBoxLayout()
        
        # Чекбокс включения функции
        enabled_checkbox = QCheckBox("Включить улучшение промтов")
        enabled_value = self.db.get_setting('prompt_improver_enabled', 'true')
        enabled_checkbox.setChecked(enabled_value.lower() in ['true', '1', 'yes'])
        improver_layout.addWidget(enabled_checkbox)
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель для улучшения промтов:"))
        model_combo = QComboBox()
        model_combo.addItem("-- Не выбрана --", None)
        
        models = self.db.get_all_models()
        current_model_id = self.db.get_setting('prompt_improver_model', '')
        
        for model in models:
            model_combo.addItem(f"{model['name']} (ID: {model['id']})", model['id'])
            if str(model['id']) == current_model_id:
                model_combo.setCurrentIndex(model_combo.count() - 1)
        
        model_layout.addWidget(model_combo)
        improver_layout.addLayout(model_layout)
        
        improver_group.setLayout(improver_layout)
        layout.addWidget(improver_group)
        
        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        def save_settings():
            # Сохраняем настройки внешнего вида
            selected_theme = theme_combo.currentData()
            self.db.set_setting('theme', selected_theme)
            
            font_size = str(font_size_spinbox.value())
            self.db.set_setting('font_size', font_size)
            
            # Сохраняем настройки улучшения промтов
            enabled = 'true' if enabled_checkbox.isChecked() else 'false'
            self.db.set_setting('prompt_improver_enabled', enabled)
            
            selected_model_id = model_combo.currentData()
            if selected_model_id:
                self.db.set_setting('prompt_improver_model', str(selected_model_id))
            else:
                self.db.set_setting('prompt_improver_model', '')
            
            # Применяем настройки
            self.apply_theme(selected_theme)
            self.apply_font_size(int(font_size))
            
            QMessageBox.information(dialog, "Успех", "Настройки сохранены!")
            dialog.accept()
        
        buttons.accepted.connect(save_settings)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_theme(self, theme: str):
        """Применить тему оформления."""
        if theme == 'dark':
            # Тёмная тема
            dark_stylesheet = """
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                background-color: transparent;
                color: #ffffff;
            }
            QTextEdit, QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #ffffff;
                selection-background-color: #0078d4;
                border: 1px solid #555555;
            }
            QCheckBox {
                background-color: transparent;
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #3c3c3c;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QTableWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                gridline-color: #555555;
                selection-background-color: #0078d4;
            }
            QTableWidget::item {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTableWidget::item:alternate {
                background-color: #353535;
            }
            QHeaderView::section {
                background-color: #2b2b2b;
                color: #ffffff;
                padding: 5px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 1px solid #555555;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            QMenu {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border-top: 1px solid #555555;
            }
            QProgressBar {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QSpinBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QSpinBox:focus {
                border: 1px solid #0078d4;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #555555;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #666666;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
            }
            QSpinBox::up-arrow {
                border-bottom: 6px solid #ffffff;
            }
            QSpinBox::down-arrow {
                border-top: 6px solid #ffffff;
            }
            """
            self.setStyleSheet(dark_stylesheet)
        else:
            # Светлая тема (по умолчанию) - сбрасываем стили
            self.setStyleSheet("")
    
    def apply_font_size(self, size: int):
        """Применить размер шрифта."""
        font = QFont()
        font.setPointSize(size)
        self.setFont(font)
        # Применяем шрифт ко всем виджетам
        for widget in self.findChildren(QWidget):
            widget.setFont(font)
    
    def _apply_theme_to_widget(self, widget: QWidget, theme: str):
        """Рекурсивно применить тему к виджету и его дочерним элементам."""
        if theme == 'dark':
            # Стили уже применены через setStyleSheet главного окна
            # Но для некоторых виджетов может потребоваться дополнительная настройка
            pass
    
    def show_about(self):
        """Показать информацию о программе."""
        about_text = """
        <h2>ChatList</h2>
        <p><b>Версия:</b> 1.0.0</p>
        <p><b>Описание:</b></p>
        <p>ChatList — это приложение для сравнения ответов различных AI-моделей на один и тот же промт.</p>
        <p>Программа позволяет:</p>
        <ul>
            <li>Отправлять промты в несколько нейросетей одновременно</li>
            <li>Сравнивать ответы разных моделей</li>
            <li>Сохранять лучшие результаты в базу данных</li>
            <li>Улучшать промты с помощью AI-ассистента</li>
            <li>Экспортировать результаты в Markdown и JSON</li>
        </ul>
        <p><b>Технологии:</b></p>
        <ul>
            <li>Python 3.12+</li>
            <li>PyQt5</li>
            <li>SQLite</li>
            <li>OpenRouter API</li>
        </ul>
        <p><b>Разработчик:</b> ChatList Team</p>
        <p><b>Лицензия:</b> MIT</p>
        """
        
        QMessageBox.about(self, "О программе", about_text)


def main():
    """Главная функция приложения."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
