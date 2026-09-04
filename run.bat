@echo off
rem ============================================================
rem  Proteo - arranque con doble clic (navegador)
rem  Crea el entorno si no existe, instala dependencias y abre
rem  la app en http://localhost:8765
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

echo [Proteo] Iniciando la aplicacion en el puerto 8765...
echo [Proteo] El navegador se abrira solo cuando el servidor responda.
echo [Proteo] Para detener Proteo, cierra esta ventana o pulsa Ctrl+C.

rem Vigilante en segundo plano: espera a que el puerto responda y ABRE el
rem navegador solo entonces (no antes).
start "" /min powershell -NoProfile -WindowStyle Hidden -Command ^
  "for ($i = 0; $i -lt 120; $i++) { try { $c = New-Object Net.Sockets.TcpClient('127.0.0.1', 8765); $c.Close(); Start-Process 'http://localhost:8765'; exit 0 } catch { Start-Sleep 1 } }"

".venv\Scripts\python.exe" -m streamlit run app\Home.py --server.headless true --browser.gatherUsageStats false --server.port 8765
if errorlevel 1 (
    echo.
    echo [Proteo] La aplicacion termino con un error. Lee el mensaje de arriba.
    pause
)
endlocal
