@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul
chcp 65001 >nul

echo [INFO] Проверка наличия Python 3...
set "PYTHON_CMD=python"
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=py -3"
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3.x не найден в PATH. Установите Python с python.org и повторите попытку.
        goto :fail
    )
)

echo [INFO] Проверка pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] pip не найден, пробую установить через ensurepip...
    %PYTHON_CMD% -m ensurepip --default-pip
    if errorlevel 1 (
        echo [ERROR] Не удалось установить pip.
        goto :fail
    )
)

echo [INFO] Обновление pip и установка зависимостей...
%PYTHON_CMD% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [OK] Python и зависимости установлены.
call :finish 0

:fail
echo [ERROR] Скрипт завершён с ошибкой. Проверьте вывод выше.
call :finish 1

:finish
popd >nul
echo.
echo Нажмите любую клавишу для закрытия окна...
pause >nul
exit /b %1
