@echo off
setlocal enabledelayedexpansion

:: Colors (Windows doesn't support ANSI colors in CMD)
set "GREEN="
set "YELLOW="
set "NC="

:: Default port
set PORT=5000

:: Parse command line arguments
:parse_args
if "%~1"=="" goto :check_args
if "%~1"=="--port" (
    set PORT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-p" (
    set PORT=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--help" (
    goto :show_help
)
if "%~1"=="-h" (
    goto :show_help
)
echo Unknown option: %~1
goto :show_help

:show_help
echo Usage: start.bat [options]
echo Options:
echo   -p, --port PORT    Specify port number (default: 5000)
echo   -h, --help         Show this help message
exit /b 0

:check_args
:: Check if port is available
netstat -an | find ":%PORT%" | find "LISTEN" >nul
if not errorlevel 1 (
    echo Port %PORT% is already in use. Please choose a different port.
    exit /b 1
)

:: Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4" ^| find /v "127.0.0.1"') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
set IP=%IP:~1%

:: Set environment variables
set FLASK_APP=src/app.py
set FLASK_ENV=development

:: Print server information
echo Starting Flask server...
echo Local URL: http://localhost:%PORT%
echo Network URL: http://%IP%:%PORT%
echo Press Ctrl+C to stop the server

:: Start the server
python src/app.py 