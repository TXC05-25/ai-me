@echo off
chcp 65001 >nul
title AI-Me Launcher

echo ========================================
echo   AI-Me · 一键启动（前后端）
echo ========================================
echo.

REM 先杀掉可能存在的旧进程
taskkill /F /IM python.exe /FI "WINDOWTITLE eq AI-Me*" 2>nul

REM 启动后端（新窗口）
start "AI-Me Backend" cmd /k "call C:\Users\谭修诚\Desktop\ai-me\start_bg.bat"

timeout /t 3 >nul

REM 启动前端（新窗口）
start "AI-Me Frontend" cmd /k "call C:\Users\谭修诚\Desktop\ai-me\start_frontend_bg.bat"

timeout /t 2 >nul

REM 打开浏览器
start "" "http://localhost:5500"

echo.
echo 服务已启动：
echo   - 后端:  http://localhost:8000
echo   - 前端:  http://localhost:5500
echo   - 文档:  http://localhost:8000/docs
echo.
echo 按任意键关闭所有服务...
pause >nul

taskkill /F /IM python.exe /FI "WINDOWTITLE eq AI-Me*" 2>nul