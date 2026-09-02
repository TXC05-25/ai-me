@echo off
REM 后台启动前端
chcp 65001 >nul
title AI-Me Frontend (Background)

cd /d "C:\Users\谭修诚\Desktop\ai-me"

echo Starting AI-Me frontend at http://localhost:5500
"D:\miniconda3\miniconda3\python.exe" -m http.server 5500 --directory "C:\Users\谭修诚\Desktop\ai-me\frontend"