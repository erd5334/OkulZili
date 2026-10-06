@echo off
chcp 65001 >nul
title Okul Zili - Windows Derleyici
echo ========================================================
echo        Okul Zili - Windows EXE ve ZIP Paketi Olusturucu
echo ========================================================
echo.
python build_windows.py
echo.
pause
