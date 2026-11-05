@echo off
chcp 65001 >nul
echo === تست نصب پایتون ===
echo.
echo where python:
where python 2>nul || echo   پیدا نشد
echo.
echo where python3:
where python3 2>nul || echo   پیدا نشد
echo.
echo where py:
where py 2>nul || echo   پیدا نشد
echo.
echo ---
python --version 2>nul || echo python --version ناموفق
python3 --version 2>nul || echo python3 --version ناموفق
py --version 2>nul || echo py --version ناموفق
echo.
pause
