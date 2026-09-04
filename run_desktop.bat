@echo off
rem ============================================================
rem  Proteo - arranque con doble clic (ventana propia)
rem  Igual que run.bat pero abre una ventana nativa en vez del
rem  navegador. Al cerrar la ventana se detiene el servidor.
rem ============================================================
chcp 65001 >nul
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [Proteo] No se encontro Python en el PATH.
    echo [Proteo] Instala Python 3.11 o superior desde https://www.python.org/downloads/
    echo [Proteo] y marca la casilla "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [Proteo] Primera ejecucion: creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo [Proteo] Fallo la creacion del entorno virtual.
        pause
        exit /b 1
    )
    echo [Proteo] Instalando dependencias. Esto tarda unos minutos, solo pasa una vez...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Proteo] Fallo la instalacion de dependencias. Revisa el error de arriba.
        pause
        exit /b 1
    )
)

echo [Proteo] Abriendo la ventana de Proteo...
".venv\Scripts\python.exe" desktop.py
if errorlevel 1 (
    echo.
    echo [Proteo] La aplicacion termino con un error. Lee el mensaje de arriba.
    pause
)
endlocal
