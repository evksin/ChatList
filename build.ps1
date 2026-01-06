# Скрипт для сборки исполняемого файла
# Убедитесь, что PyInstaller установлен: pip install pyinstaller

Write-Host "Начинаю сборку исполняемого файла..." -ForegroundColor Green

# Очистка предыдущих сборок
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build"
    Write-Host "Удалена папка build" -ForegroundColor Yellow
}

if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "Удалена папка dist" -ForegroundColor Yellow
}

# Сборка исполняемого файла
# --onefile - создает один исполняемый файл
# --windowed - скрывает консольное окно (для GUI приложений)
# --name - имя выходного файла
pyinstaller --onefile --windowed --name "PyQtApp" main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nСборка завершена успешно!" -ForegroundColor Green
    Write-Host "Исполняемый файл находится в папке: dist\PyQtApp.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nОшибка при сборке!" -ForegroundColor Red
}



