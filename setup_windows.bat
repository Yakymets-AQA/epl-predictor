@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul
chcp 65001 >nul

echo [INFO] Проверка наличия Python 3...
set "PYTHON_EXE=python"
set "PYTHON_ARGS="
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
    "%PYTHON_EXE%" %PYTHON_ARGS% --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3.x не найден в PATH. Установите Python с python.org и повторите попытку.
        goto :fail
    )
)

set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [INFO] Создание виртуального окружения...
    "%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%VENV_DIR%"
    if errorlevel 1 goto :fail
)

echo [INFO] Проверка pip в виртуальном окружении...
"%VENV_PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] pip не найден в виртуальном окружении, пробую установить через ensurepip...
    "%VENV_PY%" -m ensurepip --default-pip
    if errorlevel 1 (
        echo [ERROR] Не удалось установить pip.
        goto :fail
    )
)

echo [INFO] Обновление pip и установка зависимостей...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [OK] Python и зависимости установлены. Виртуальное окружение: %VENV_DIR%.
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
