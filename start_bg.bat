@echo off
REM 后台启动 AI-Me（独立进程，不依赖父窗口）
chcp 65001 >nul
title AI-Me Backend (Background)

cd /d "C:\Users\谭修诚\Desktop\ai-me"

echo Starting AI-Me backend at http://localhost:8001
"D:\miniconda3\miniconda3\python.exe" "C:\Users\谭修诚\Desktop\ai-me\backend\main.py"