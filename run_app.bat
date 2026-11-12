@echo off
TITLE PrepAI - AI Interview Preparation System
echo ===================================================
echo Starting PrepAI - AI Interview Preparation System
echo ===================================================
echo.

IF EXIST ..\.venv\Scripts\streamlit.exe (
    echo Using project virtual environment...
    ..\.venv\Scripts\streamlit.exe run app.py
) ELSE IF EXIST .venv\Scripts\streamlit.exe (
    echo Using local virtual environment...
    .venv\Scripts\streamlit.exe run app.py
) ELSE (
    echo Using system Python streamlit...
    streamlit run app.py
)

pause
