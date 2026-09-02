@echo off
chcp 65001 >nul
title AI-Me Dev Launcher

echo ========================================
echo   AI-Me · 一键启动
echo ========================================
echo.
echo   这个脚本会同时启动：
echo   - 后端 FastAPI (端口 8000)
echo   - 前端静态服务 (端口 5500)
echo.
echo   需要 miniconda3 的 Python，已为你配置好
echo.

REM 切换到项目根目录
cd /d "%~dp0"

REM 检查 .env 文件
if not exist ".env" (
    echo [WARN] .env 不存在
    echo [INFO] 从 .env.example 复制
    copy /Y .env.example .env >nul
    echo [INFO] 请编辑 .env 填入 LLM_API_KEY / EMBEDDING_API_KEY / RERANK_API_KEY
    echo.
    pause
)

REM miniconda Python 路径
set PYTHON=D:\miniconda3\miniconda3\python.exe
if not exist "%PYTHON%" (
    echo [ERROR] miniconda3 Python 未找到: %PYTHON%
    echo [INFO] 请修改 start.bat 中的 PYTHON 变量为你机器上的 Python 路径
    pause
    exit /b 1
)

echo [1/3] 启动后端 (端口 8000)...
start "AI-Me Backend" cmd /k "cd /d %~dp0\backend && %PYTHON% main.py"

timeout /t 3 >nul

echo [2/3] 启动前端 (端口 5500)...
start "AI-Me Frontend" cmd /k "cd /d %~dp0\frontend && %PYTHON% -m http.server 5500"

timeout /t 2 >nul

echo.
echo [3/3] 打开浏览器...
start "" "http://localhost:5500"

echo.
echo ========================================
echo   启动完成！
echo
   - 后端： http://localhost:8000
   - 前端： http://localhost:5500
   - API 文档： http://localhost:8000/docs
   - 健康检查： http://localhost:8000/health
echo ========================================
echo.
echo   如果聊天显示「Failed to fetch」：
echo   1. 确认两个 cmd 窗口都还在
echo   2. 检查后端窗口是否报错
echo   3. 在浏览器按 F12 看 Network 请求
echo.
echo   关闭时直接关掉两个 cmd 窗口即可
echo.
pause