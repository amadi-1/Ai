@echo off
cd /d "%~dp0"
title Option Server
color 0A

echo ========================================
echo   سرور اپ آپشن - سینو بورس
echo ========================================
echo.
echo پوشه:
echo %CD%
echo.

echo در حال پیدا کردن پایتون...
echo.

set PY=

where python >nul 2>&1
if %errorlevel%==0 (
  echo [OK] python پیدا شد
  set PY=python
  goto found
)

where py >nul 2>&1
if %errorlevel%==0 (
  echo [OK] py پیدا شد
  set PY=py
  goto found
)

where python3 >nul 2>&1
if %errorlevel%==0 (
  echo [OK] python3 پیدا شد
  set PY=python3
  goto found
)

echo.
echo ========================================
echo  ERROR: پایتون پیدا نشد!
echo ========================================
echo.
echo پایتون روی سیستم شما نصب نیست
echo یا در PATH قرار ندارد.
echo.
echo راه حل:
echo  1. برو به https://www.python.org/downloads/
echo  2. Download Python را بزن
echo  3. موقع نصب تیک این گزینه را فعال کن:
echo.
echo      Add python.exe to PATH
echo.
echo  4. نصب را تمام کن و کامپیوتر را Restart کن
echo  5. دوباره این فایل را اجرا کن
echo.
echo ========================================
goto end

:found
echo.
echo نسخه:
%PY% --version
echo.
echo در حال اجرای سرور...
echo.
echo ----------------------------------------
echo  بعد از آماده شدن، در مرورگر باز کن:
echo.
echo     http://127.0.0.1:8080
echo.
echo  این پنجره را نبند!
echo ----------------------------------------
echo.

%PY% server.py

echo.
echo.
echo سرور بسته شد.
echo کد خروجی: %ERRORLEVEL%
echo.

:end
echo.
echo برای بستن این پنجره کلیدی بزنید...
pause >nul
