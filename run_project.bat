@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%" >nul
chcp 65001 >nul

set "VENV_PY=%SCRIPT_DIR%.venv\Scripts\python.exe"
if exist "%VENV_PY%" (
    set "PYTHON_EXE=%VENV_PY%"
    set "PYTHON_ARGS="
) else (
    set "PYTHON_EXE=python"
    set "PYTHON_ARGS="
    "%PYTHON_EXE%" --version >nul 2>&1
    if errorlevel 1 (
        set "PYTHON_EXE=py"
        set "PYTHON_ARGS=-3"
        "%PYTHON_EXE%" %PYTHON_ARGS% --version >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Python 3 не найден. Установите Python или запустите setup_windows.bat.
            goto :fail
        )
    )
)

set "ROUND=%~1"
if "%ROUND%"=="" (
    set /p ROUND="Введите номер тура и нажмите Enter: "
    if "%ROUND%"=="" (
        echo [ERROR] Номер тура не указан.
        goto :fail
    )
)
set "RAW_RESULTS=data\raw_results_template.txt"
set "RESULTS_CSV=data\results_sample.csv"
set "RAW_PREDICTIONS=data\raw_predictions_template.txt"
set "PREDICTIONS_CSV=data\predictions_sample.csv"
set "OUTPUT_XLSX=output\apl_standings.xlsx"

echo [INFO] Нормализация шаблона результатов...
"%PYTHON_EXE%" %PYTHON_ARGS% scripts\normalize_text_matches.py "%RAW_RESULTS%"
if errorlevel 1 goto :fail

echo [INFO] Импорт результатов тура %ROUND%...
"%PYTHON_EXE%" %PYTHON_ARGS% scripts\import_text_results.py "%RAW_RESULTS%" "%RESULTS_CSV%" --round "%ROUND%"
if errorlevel 1 goto :fail

echo [INFO] Нормализация шаблона прогнозов...
"%PYTHON_EXE%" %PYTHON_ARGS% scripts\normalize_text_matches.py "%RAW_PREDICTIONS%"
if errorlevel 1 goto :fail

echo [INFO] Импорт прогнозов пользователей...
"%PYTHON_EXE%" %PYTHON_ARGS% scripts\import_text_predictions.py "%RAW_PREDICTIONS%" "%RESULTS_CSV%" "%PREDICTIONS_CSV%" --clear-users
if errorlevel 1 goto :fail

echo [INFO] Пересчет турнирной таблицы...
"%PYTHON_EXE%" %PYTHON_ARGS% scripts\generate_scoreboard.py "%PREDICTIONS_CSV%" "%RESULTS_CSV%" "%OUTPUT_XLSX%"
if errorlevel 1 goto :fail

echo [OK] Проект выполнен. Файл таблицы: %OUTPUT_XLSX%.
call :finish 0

:fail
echo [ERROR] Выполнение остановлено из-за ошибки на одном из шагов.
call :finish 1

:finish
popd >nul
echo.
echo Нажмите любую клавишу для закрытия окна...
pause >nul
exit /b %1
