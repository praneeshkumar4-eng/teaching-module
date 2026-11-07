# LessonForge Launch Script for PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting LessonForge - AI Lesson Creation Suite..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

& ".\.venv\Scripts\streamlit.exe" run app.py

