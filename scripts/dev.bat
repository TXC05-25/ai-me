@echo off
REM ============================================
REM AI-Me · Windows 一键开发启动
REM ============================================
chcp 65001 >nul
title AI-Me Dev

echo ========================================
echo   AI-Me 开发环境启动
echo ========================================
echo.

REM 激活虚拟环境
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] 虚拟环境已激活
) else (
    echo [WARN] .venv 不存在，使用全局 Python
)

REM 检查 .env
if not exist .env (
    echo [WARN] .env 不存在，从 .env.example 复制
    copy .env.example .env
    echo [INFO] 请编辑 .env 填入 API Key
    pause
)

REM 启动后端
echo.
echo [1/2] 启动后端 (端口 8000)...
start "AI-Me Backend" cmd /k "cd /d %~dp0\backend && python main.py"

REM 启动前端
echo [2/2] 启动前端 (端口 5500)...
start "AI-Me Frontend" cmd /k "cd /d %~dp0\frontend && python -m http.server 5500"

echo.
echo ========================================
echo   启动完成
echo   - 后端：http://localhost:8000/docs
echo   - 前端：http://localhost:5500
echo ========================================
echo.
pause