@echo off
echo Starting CPU Simulator Server...
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Running tests...
python tests\test_cpu.py
echo.
echo Starting Django server...
echo Open your browser to: http://localhost:8000
echo.
python manage.py runserver

