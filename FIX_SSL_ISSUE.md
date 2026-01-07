# Решение проблемы с SSL ошибками

## Проблема
Вы получаете ошибки `SSLEOFError: EOF occurred in violation of protocol` при подключении к OpenRouter API.

## Причина
Используется Python 3.9 с устаревшим OpenSSL 1.1.1l, который может иметь проблемы с некоторыми SSL соединениями.

## Решения

### Решение 1: Использовать Python 3.12 (РЕКОМЕНДУЕТСЯ)

У вас установлен Python 3.12, который имеет более новую версию OpenSSL:

```powershell
# Проверьте, что Python 3.12 используется
py -3.12 --version

# Запустите приложение с Python 3.12
py -3.12 main.py
```

Или установите Python 3.12 как версию по умолчанию:
```powershell
# В PowerShell от администратора
[Environment]::SetEnvironmentVariable("Path", "C:\Python312;C:\Python312\Scripts;" + [Environment]::GetEnvironmentVariable("Path", "Machine"), "Machine")
```

### Решение 2: Временно отключить проверку SSL (для диагностики)

⚠️ **ВНИМАНИЕ:** Это снижает безопасность. Используйте только для диагностики!

1. Добавьте в файл `.env`:
   ```
   DISABLE_SSL_VERIFY=true
   ```

2. Перезапустите приложение

3. Если это помогло, значит проблема в SSL. Рекомендуется использовать Python 3.12.

### Решение 3: Обновить OpenSSL в Python 3.9

Это сложнее и может не помочь. Лучше использовать Python 3.12.

## Проверка

После применения решения проверьте:

```powershell
# Проверка версии Python и OpenSSL
python -c "import ssl; print(ssl.OPENSSL_VERSION)"

# Проверка подключения
python -c "import requests; r = requests.get('https://openrouter.ai/api/v1/models', timeout=5); print(f'Status: {r.status_code}')"
```

## Рекомендация

**Используйте Python 3.12** - это самое простое и правильное решение. Python 3.9 с OpenSSL 1.1.1l устарел и может иметь проблемы с современными SSL соединениями.


