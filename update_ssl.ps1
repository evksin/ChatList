# Скрипт для обновления SSL сертификатов в Windows
# Запустите от имени администратора

Write-Host "Обновление SSL сертификатов..." -ForegroundColor Green

# Обновление сертификатов через Windows Update
Write-Host "`n1. Проверка обновлений Windows..." -ForegroundColor Yellow
$updateSession = New-Object -ComObject Microsoft.Update.Session
$updateSearcher = $updateSession.CreateUpdateSearcher()
$searchResult = $updateSearcher.Search("IsInstalled=0 and Type='Software'")

if ($searchResult.Updates.Count -gt 0) {
    Write-Host "Найдено обновлений: $($searchResult.Updates.Count)" -ForegroundColor Cyan
    Write-Host "Рекомендуется установить обновления Windows через Центр обновления Windows" -ForegroundColor Yellow
} else {
    Write-Host "Обновления не найдены или уже установлены" -ForegroundColor Green
}

# Обновление Python пакетов, связанных с SSL
Write-Host "`n2. Обновление Python пакетов..." -ForegroundColor Yellow
python -m pip install --upgrade certifi requests urllib3

# Проверка версии certifi
Write-Host "`n3. Проверка установленных пакетов..." -ForegroundColor Yellow
python -c "import certifi; print(f'certifi: {certifi.__version__}'); import ssl; print(f'SSL версия: {ssl.OPENSSL_VERSION}')"

# Обновление сертификатов certifi
Write-Host "`n4. Обновление сертификатов certifi..." -ForegroundColor Yellow
python -c "import certifi; import urllib.request; urllib.request.urlretrieve('https://curl.se/ca/cacert.pem', certifi.where())"

Write-Host "`nГотово! Перезапустите приложение." -ForegroundColor Green
Write-Host "`nЕсли проблема сохраняется, попробуйте:" -ForegroundColor Yellow
Write-Host "1. Обновить Windows через Центр обновления" -ForegroundColor White
Write-Host "2. Проверить настройки прокси/файрвола" -ForegroundColor White
Write-Host "3. Временно отключить проверку SSL (не рекомендуется)" -ForegroundColor White

