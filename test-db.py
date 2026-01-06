"""
Тестовая программа для просмотра SQLite-базы данных.

Функции:
- выбор файла БД;
- отображение списка таблиц;
- кнопка «Открыть» для выбранной таблицы;
- просмотр содержимого таблицы с пагинацией;
- кнопки CRUD (Create, Read/Refresh, Update, Delete) для строк.
"""

import sys
import os
import sqlite3
from typing import List, Any, Optional

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QSpinBox,
)
from PyQt5.QtCore import Qt


class RowEditDialog(QDialog):
    """Диалог для добавления/редактирования строки таблицы."""

    def __init__(self, columns: List[str], values: Optional[List[Any]] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование строки" if values else "Добавление строки")
        self.columns = columns
        self.edits: List[QLineEdit] = []

        layout = QVBoxLayout()

        for i, col in enumerate(columns):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(col + ":"))
            edit = QLineEdit()
            if values is not None and i < len(values):
                edit.setText("" if values[i] is None else str(values[i]))
            row_layout.addWidget(edit)
            self.edits.append(edit)
            layout.addLayout(row_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self) -> List[str]:
        return [edit.text() for edit in self.edits]


class TestDbWindow(QMainWindow):
    """Главное окно тестовой программы для работы с SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Test DB Viewer")
        self.setGeometry(100, 100, 1000, 700)

        self.conn: Optional[sqlite3.Connection] = None
        self.current_table: Optional[str] = None
        self.page_size = 50
        self.current_page = 0
        self.total_rows = 0

        self._init_ui()

        if db_path and os.path.exists(db_path):
            self.load_database(db_path)
        else:
            # Попробуем автоматически открыть chatlist.db, если есть
            default_db = os.path.join(os.getcwd(), "chatlist.db")
            if os.path.exists(default_db):
                self.load_database(default_db)

    # ---------- UI ----------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Панель выбора файла БД
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Файл БД:"))
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setReadOnly(True)
        db_layout.addWidget(self.db_path_edit)
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self.select_db_file)
        db_layout.addWidget(browse_btn)
        main_layout.addLayout(db_layout)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # Левая панель – список таблиц
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Таблицы:"))
        self.tables_list = QListWidget()
        left_layout.addWidget(self.tables_list)
        open_btn = QPushButton("Открыть таблицу")
        open_btn.clicked.connect(self.open_selected_table)
        left_layout.addWidget(open_btn)
        content_layout.addLayout(left_layout, 1)

        # Правая панель – таблица данных и управление
        right_layout = QVBoxLayout()

        # Пагинация
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("<<")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton(">>")
        self.next_btn.clicked.connect(self.next_page)
        self.page_label = QLabel("Страница: 1 / 1")

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addStretch()

        pagination_layout.addWidget(QLabel("На странице:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(10, 1000)
        self.page_size_spin.setValue(self.page_size)
        self.page_size_spin.valueChanged.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_spin)

        right_layout.addLayout(pagination_layout)

        # Таблица
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SingleSelection)
        right_layout.addWidget(self.data_table, 1)

        # Кнопки CRUD
        crud_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_row)
        self.edit_btn = QPushButton("Изменить")
        self.edit_btn.clicked.connect(self.edit_row)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_row)
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.reload_current_table)

        for btn in (self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn):
            crud_layout.addWidget(btn)
        crud_layout.addStretch()
        right_layout.addLayout(crud_layout)

        content_layout.addLayout(right_layout, 3)

        # Изначально кнопки таблицы неактивны
        self.set_table_controls_enabled(False)

    # ---------- Работа с БД ----------

    def select_db_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл SQLite", os.getcwd(), "SQLite DB (*.db *.sqlite *.sqlite3);;Все файлы (*.*)"
        )
        if file_path:
            self.load_database(file_path)

    def load_database(self, path: str):
        try:
            if self.conn:
                self.conn.close()
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.db_path_edit.setText(path)
            self.statusBar().showMessage(f"Открыта база данных: {path}")
            self.load_tables()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось открыть базу данных:\n{e}")
            self.conn = None

    def load_tables(self):
        if not self.conn:
            return
        try:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            tables = [row[0] for row in cur.fetchall()]
            self.tables_list.clear()
            self.tables_list.addItems(tables)
            self.current_table = None
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            self.set_table_controls_enabled(False)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось получить список таблиц:\n{e}")

    def open_selected_table(self):
        item = self.tables_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Предупреждение", "Выберите таблицу из списка.")
            return
        table = item.text()
        self.open_table(table)

    def open_table(self, table: str):
        if not self.conn:
            return
        self.current_table = table
        self.current_page = 0
        self.update_total_rows()
        self.load_page()
        self.set_table_controls_enabled(True)
        self.setWindowTitle(f"Test DB Viewer – {table}")

    def update_total_rows(self):
        if not self.conn or not self.current_table:
            self.total_rows = 0
            return
        cur = self.conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {self.current_table}")
        self.total_rows = cur.fetchone()[0]

    def load_page(self):
        if not self.conn or not self.current_table:
            return

        self.page_size = self.page_size_spin.value()
        offset = self.current_page * self.page_size

        cur = self.conn.cursor()
        # Получаем имена столбцов
        cur.execute(f"PRAGMA table_info({self.current_table})")
        columns_info = cur.fetchall()
        columns = [col[1] for col in columns_info]

        # Получаем данные
        cur.execute(
            f"SELECT * FROM {self.current_table} LIMIT {self.page_size} OFFSET {offset}"
        )
        rows = cur.fetchall()

        self.data_table.setColumnCount(len(columns))
        self.data_table.setHorizontalHeaderLabels(columns)
        self.data_table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, col_name in enumerate(columns):
                value = row[col_name]
                item = QTableWidgetItem("" if value is None else str(value))
                self.data_table.setItem(r, c, item)

        # Обновляем пагинацию
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        current_page_display = self.current_page + 1
        self.page_label.setText(f"Страница: {current_page_display} / {total_pages} (записей: {self.total_rows})")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

    # ---------- Пагинация ----------

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.load_page()

    def on_page_size_changed(self, value: int):
        self.page_size = value
        self.current_page = 0
        self.load_page()

    # ---------- CRUD ----------

    def get_current_columns(self) -> List[str]:
        return [
            self.data_table.horizontalHeaderItem(i).text()
            for i in range(self.data_table.columnCount())
        ]

    def add_row(self):
        if not self.conn or not self.current_table:
            return
        columns = self.get_current_columns()
        dlg = RowEditDialog(columns, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            values = dlg.get_values()
            placeholders = ", ".join(["?"] * len(columns))
            cols_sql = ", ".join(columns)
            try:
                cur = self.conn.cursor()
                cur.execute(
                    f"INSERT INTO {self.current_table} ({cols_sql}) VALUES ({placeholders})",
                    values,
                )
                self.conn.commit()
                self.update_total_rows()
                self.load_page()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось добавить запись:\n{e}")

    def edit_row(self):
        if not self.conn or not self.current_table:
            return
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для редактирования.")
            return

        columns = self.get_current_columns()
        current_values = [
            self.data_table.item(row_idx, c).text() if self.data_table.item(row_idx, c) else ""
            for c in range(len(columns))
        ]

        dlg = RowEditDialog(columns, current_values, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_values = dlg.get_values()

            # Предполагаем, что первый столбец – первичный ключ
            pk_column = columns[0]
            pk_value = current_values[0]
            set_clause = ", ".join([f"{col}=?" for col in columns[1:]])
            params = new_values[1:] + [pk_value]

            try:
                cur = self.conn.cursor()
                cur.execute(
                    f"UPDATE {self.current_table} SET {set_clause} WHERE {pk_column} = ?",
                    params,
                )
                self.conn.commit()
                self.load_page()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось обновить запись:\n{e}")

    def delete_row(self):
        if not self.conn or not self.current_table:
            return
        row_idx = self.data_table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите строку для удаления.")
            return

        columns = self.get_current_columns()
        pk_column = columns[0]
        pk_item = self.data_table.item(row_idx, 0)
        if not pk_item:
            QMessageBox.warning(self, "Предупреждение", "Не удалось определить первичный ключ.")
            return
        pk_value = pk_item.text()

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить запись с {pk_column} = {pk_value}?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            cur = self.conn.cursor()
            cur.execute(
                f"DELETE FROM {self.current_table} WHERE {pk_column} = ?",
                (pk_value,),
            )
            self.conn.commit()
            self.update_total_rows()
            # Если текущая страница стала пустой, переходим на предыдущую
            total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)
            self.load_page()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить запись:\n{e}")

    def reload_current_table(self):
        if not self.current_table:
            return
        self.update_total_rows()
        self.load_page()

    def set_table_controls_enabled(self, enabled: bool):
        for w in (self.add_btn, self.edit_btn, self.delete_btn, self.refresh_btn,
                  self.prev_btn, self.next_btn, self.data_table):
            w.setEnabled(enabled)


def main():
    app = QApplication(sys.argv)
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    window = TestDbWindow(db_path)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


