# Схема базы данных ChatList

База данных использует SQLite и состоит из четырёх основных таблиц.

## Таблица: prompts

Хранит сохранённые промты (запросы) пользователя.

| Поле   | Тип     | Описание                         | Ограничения                         |
| ------ | ------- | -------------------------------- | ----------------------------------- |
| id     | INTEGER | Первичный ключ                   | PRIMARY KEY, AUTOINCREMENT          |
| date   | TEXT    | Дата и время создания промта     | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| prompt | TEXT    | Текст промта                     | NOT NULL                            |
| tags   | TEXT    | Теги через запятую (опционально) | NULL                                |

**Индексы:**

- `idx_prompts_date` на поле `date` (для сортировки по дате)
- `idx_prompts_tags` на поле `tags` (для поиска по тегам)

**Примеры запросов:**

- Получить все промты, отсортированные по дате
- Найти промты по тегу
- Поиск промтов по тексту

---

## Таблица: models

Хранит информацию о нейросетевых моделях и их API-конфигурации.

| Поле      | Тип     | Описание                                                                     | Ограничения                |
| --------- | ------- | ---------------------------------------------------------------------------- | -------------------------- |
| id        | INTEGER | Первичный ключ                                                               | PRIMARY KEY, AUTOINCREMENT |
| name      | TEXT    | Название модели (например, "GPT-4", "DeepSeek Chat")                         | NOT NULL, UNIQUE           |
| api_url   | TEXT    | URL API для отправки запросов                                                | NOT NULL                   |
| api_id    | TEXT    | Идентификатор переменной окружения с API-ключом (например, "OPENAI_API_KEY") | NOT NULL                   |
| is_active | INTEGER | Флаг активности модели (1 - активна, 0 - неактивна)                          | NOT NULL, DEFAULT 1        |

**Индексы:**

- `idx_models_active` на поле `is_active` (для быстрого получения активных моделей)

**Примечания:**

- API-ключи хранятся в файле `.env`, а не в базе данных
- Поле `api_id` содержит имя переменной окружения, которая будет использоваться для получения ключа из `.env`
- Поле `is_active` позволяет временно отключать модели без удаления из БД

**Примеры запросов:**

- Получить все активные модели: `SELECT * FROM models WHERE is_active = 1`
- Активировать/деактивировать модель
- Добавить новую модель с указанием её API-конфигурации

---

## Таблица: results

Хранит сохранённые результаты ответов моделей на промты.

| Поле      | Тип     | Описание                                              | Ограничения                                              |
| --------- | ------- | ----------------------------------------------------- | -------------------------------------------------------- |
| id        | INTEGER | Первичный ключ                                        | PRIMARY KEY, AUTOINCREMENT                               |
| prompt_id | INTEGER | Ссылка на промт из таблицы prompts                    | NOT NULL, FOREIGN KEY (prompt_id) REFERENCES prompts(id) |
| model_id  | INTEGER | Ссылка на модель из таблицы models                    | NOT NULL, FOREIGN KEY (model_id) REFERENCES models(id)   |
| response  | TEXT    | Текст ответа от модели                                | NOT NULL                                                 |
| date      | TEXT    | Дата и время получения ответа                         | NOT NULL, DEFAULT CURRENT_TIMESTAMP                      |
| selected  | INTEGER | Флаг выбора пользователем (1 - выбран, 0 - не выбран) | NOT NULL, DEFAULT 0                                      |

**Индексы:**

- `idx_results_prompt` на поле `prompt_id` (для поиска результатов по промту)
- `idx_results_model` на поле `model_id` (для поиска результатов по модели)
- `idx_results_date` на поле `date` (для сортировки по дате)
- `idx_results_selected` на поле `selected` (для фильтрации выбранных результатов)

**Связи:**

- `prompt_id` → `prompts.id` (ON DELETE CASCADE - при удалении промта удаляются связанные результаты)
- `model_id` → `models.id` (ON DELETE RESTRICT - нельзя удалить модель, если есть результаты)

**Примеры запросов:**

- Получить все результаты для конкретного промта
- Получить все выбранные результаты
- Найти результаты конкретной модели
- Экспортировать выбранные результаты

---

## Таблица: settings

Хранит настройки программы в формате ключ-значение.

| Поле  | Тип  | Описание           | Ограничения                   |
| ----- | ---- | ------------------ | ----------------------------- |
| key   | TEXT | Ключ настройки     | PRIMARY KEY, NOT NULL, UNIQUE |
| value | TEXT | Значение настройки | NOT NULL                      |

**Примеры настроек:**

- `default_timeout` - таймаут для HTTP-запросов (по умолчанию: "30")
- `max_response_length` - максимальная длина ответа для отображения (по умолчанию: "10000")
- `auto_save` - автоматическое сохранение результатов (по умолчанию: "false")
- `theme` - тема интерфейса (по умолчанию: "light")
- `export_format` - формат экспорта по умолчанию (по умолчанию: "markdown")

**Примеры запросов:**

- Получить значение настройки: `SELECT value FROM settings WHERE key = 'default_timeout'`
- Установить настройку: `INSERT OR REPLACE INTO settings (key, value) VALUES ('default_timeout', '60')`
- Получить все настройки

---

## Диаграмма связей

```
prompts (1) ──< (N) results
models (1) ──< (N) results
settings (независимая таблица)
```

---

## Инициализация базы данных

При первом запуске программы создаются все таблицы с указанными полями, индексами и ограничениями.

**SQL для создания таблиц:**

```sql
-- Таблица prompts
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    prompt TEXT NOT NULL,
    tags TEXT
);

-- Таблица models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- Таблица results
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response TEXT NOT NULL,
    date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    selected INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE RESTRICT
);

-- Таблица settings
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY NOT NULL UNIQUE,
    value TEXT NOT NULL
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id);
CREATE INDEX IF NOT EXISTS idx_results_date ON results(date);
CREATE INDEX IF NOT EXISTS idx_results_selected ON results(selected);
```

---

## Примеры данных

### prompts

```
id | date                | prompt                    | tags
1  | 2024-01-15 10:30:00 | Объясни квантовую физику  | физика, наука
2  | 2024-01-15 11:00:00 | Напиши код на Python      | программирование
```

### models

```
id | name          | api_url                    | api_id          | is_active
1  | GPT-4         | https://api.openai.com/... | OPENAI_API_KEY  | 1
2  | DeepSeek Chat | https://api.deepseek.com/.. | DEEPSEEK_API_KEY| 1
3  | Groq Llama    | https://api.groq.com/...   | GROQ_API_KEY    | 0
```

### results

```
id | prompt_id | model_id | response           | date                | selected
1  | 1         | 1        | Квантовая физика...| 2024-01-15 10:31:00 | 1
2  | 1         | 2        | Квантовая механика...| 2024-01-15 10:31:05 | 0
```

### settings

```
key                | value
default_timeout    | 30
max_response_length| 10000
auto_save          | false
theme              | light
```
