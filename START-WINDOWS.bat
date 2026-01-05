@echo off
echo ========================================
echo   Cafe Menu Scraper - Web Interface
echo ========================================
echo.
echo Starting the web server...
echo.
echo IMPORTANT: Keep this window open!
echo.
echo Opening your web browser...
echo Go to: http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo ========================================
echo.

start http://localhost:5000

python web_app.py

pause
