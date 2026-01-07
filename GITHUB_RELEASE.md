# Инструкция по публикации на GitHub Release

## Подготовка

### 1. Создание релиза

Перед созданием релиза убедитесь, что:

- ✅ Версия обновлена в `version.py`
- ✅ Исполняемый файл собран: `dist\ChatList-v{version}.exe`
- ✅ Инсталлятор создан: `installer\ChatList-Setup-v{version}.exe`
- ✅ Все изменения закоммичены и запушены в репозиторий

### 2. Создание тега версии

```powershell
# Получить текущую версию
$version = python -c "from version import __version__; print(__version__)"

# Создать тег
git tag -a "v$version" -m "Release version $version"

# Отправить тег на GitHub
git push origin "v$version"
```

Или вручную через Git:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Создание Release на GitHub

### Способ 1: Через веб-интерфейс GitHub

1. Перейдите на страницу репозитория: `https://github.com/yourusername/chatlist`
2. Нажмите на **"Releases"** в правой панели
3. Нажмите **"Create a new release"** или **"Draft a new release"**
4. Заполните форму:
   - **Tag version**: Выберите созданный тег (например, `v1.0.0`)
   - **Release title**: `ChatList v1.0.0` или `Release v1.0.0`
   - **Description**: Используйте шаблон из `RELEASE_NOTES_TEMPLATE.md` или создайте свой
5. Загрузите файлы:
   - **Installer**: `installer\ChatList-Setup-v1.0.0.exe`
   - **Executable** (опционально): `dist\ChatList-v1.0.0.exe`
6. Нажмите **"Publish release"**

### Способ 2: Через GitHub CLI (gh)

```powershell
# Установите GitHub CLI, если ещё не установлен
# winget install GitHub.cli

# Авторизуйтесь
gh auth login

# Создайте релиз
$version = python -c "from version import __version__; print(__version__)"
$releaseNotes = Get-Content "RELEASE_NOTES_TEMPLATE.md" -Raw

gh release create "v$version" `
    "installer\ChatList-Setup-v$version.exe" `
    "dist\ChatList-v$version.exe" `
    --title "ChatList v$version" `
    --notes "$releaseNotes"
```

### Способ 3: Автоматически через скрипт

Используйте скрипт `create_release.ps1`:

```powershell
.\create_release.ps1
```

## Структура Release Notes

Используйте шаблон из `RELEASE_NOTES_TEMPLATE.md`:

- **Заголовок** с версией
- **Дата релиза**
- **Что нового** (новые функции)
- **Улучшения** (улучшения существующих функций)
- **Исправления** (исправленные баги)
- **Технические детали** (изменения в зависимостях, архитектуре)
- **Скачать** (ссылки на файлы)

## Рекомендации

1. **Семантическое версионирование**: Используйте формат `MAJOR.MINOR.PATCH` (например, `1.0.0`)
2. **Чанклоги**: Ведите файл `CHANGELOG.md` для отслеживания изменений
3. **Теги**: Всегда создавайте теги перед релизом
4. **Проверка**: Перед публикацией проверьте, что инсталлятор работает корректно

## Автоматизация

Для автоматической публикации можно использовать GitHub Actions (см. `.github/workflows/release.yml`).

