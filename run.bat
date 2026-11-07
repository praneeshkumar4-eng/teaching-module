@echo off
echo ========================================================
echo Starting LessonForge - AI Lesson Creation Suite...
echo ========================================================
call .\.venv\Scripts\activate.bat
streamlit run app.py
pause

