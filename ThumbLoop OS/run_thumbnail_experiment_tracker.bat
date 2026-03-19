@echo off
cd /d "%~dp0"

echo [1/2] Python 확인
python --version
if errorlevel 1 (
    echo Python 실행 불가
    pause
    exit /b 1
)

echo [2/2] thumbnail_experiment_tracker.py 실행
python thumbnail_experiment_tracker.py

echo.
echo 완료되었습니다.
pause