@echo off
cd /d "%~dp0"

echo [1/3] Python 확인
python --version
if errorlevel 1 (
    echo Python 실행 불가
    pause
    exit /b 1
)

echo [2/3] Pillow 설치 확인
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo Pillow 미설치. 설치를 시작합니다.
    pip install pillow
)

echo [3/3] thumbnail_renderer.py 실행
python thumbnail_renderer.py

echo.
echo 완료되었습니다.
pause