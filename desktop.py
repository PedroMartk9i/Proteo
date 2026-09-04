"""Ventana nativa de Proteo (pywebview).

Arranca Streamlit en un subproceso, espera a que el puerto responda,
abre una ventana de 1400x900 titulada "Proteo" y, al cerrarla, termina
el subproceso (con todo su árbol, para no dejar procesos vivos).
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8765


def wait_for_port(port: int, timeout: float = 120.0) -> bool:
    """Espera a que el puerto acepte conexiones. True si respondió."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def start_streamlit() -> subprocess.Popen:
    """Lanza el servidor de Streamlit como subproceso."""
    python = ROOT / ".venv" / "Scripts" / "python.exe"
    if not python.exists():
        python = Path(sys.executable)
    return subprocess.Popen(
        [
            str(python), "-m", "streamlit", "run", "app/Home.py",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
            "--server.port", str(PORT),
        ],
        cwd=ROOT,
    )


def stop_streamlit(proc: subprocess.Popen) -> None:
    """Termina el subproceso y su árbol completo (Windows)."""
    if proc.poll() is not None:
        return
    subprocess.run(
        ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
        capture_output=True,
    )
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> None:
    import webview  # import tardío: solo hace falta para la ventana

    proc = start_streamlit()
    try:
        if not wait_for_port(PORT):
            print(f"[Proteo] Streamlit no respondió en el puerto {PORT}.")
            sys.exit(1)
        webview.create_window(
            "Proteo", f"http://127.0.0.1:{PORT}", width=1400, height=900
        )
        webview.start()
    finally:
        stop_streamlit(proc)


if __name__ == "__main__":
    main()
