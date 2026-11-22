"""
Organizer App — Orquestrador Unificado de Inicialização Full-Stack
Sobe toda a aplicação com um único comando:
  - Backend FastAPI (Porta 8000)
  - Frontend React / Vite (Porta 5173)
  - Suplemento Microsoft Excel Add-in (Porta 3000)

Uso:
  python start.py           (Execução nativa concorrente)
  python start.py --docker   (Execução containerizada via Docker Compose)
"""

import os
import sys
import time
import shutil
import signal
import urllib.request
import subprocess
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
ADDIN_DIR = ROOT_DIR / "excel-addin"

IS_WINDOWS = sys.platform.startswith("win")
CHILD_PROCESSES = []
TERMINATING = False


def check_docker_running() -> bool:
    """Verifica se o daemon do Docker está acessível."""
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )
        return res.returncode == 0
    except Exception:
        return False


def run_with_docker():
    """Inicia os contêineres via docker compose."""
    print("\n" + "=" * 70)
    print("🐳 INICIANDO ORGANIZER APP VIA DOCKER COMPOSE")
    print("=" * 70)

    if not check_docker_running():
        print("⚠️  AVISO: O daemon do Docker Desktop não está em execução ou não respondeu.")
        print("💡 Alternando automaticamente para o modo nativo local (sem Docker)...\n")
        run_native()
        return

    try:
        cmd = ["docker", "compose", "up", "--build"]
        print(f"Executando: {' '.join(cmd)}\n")
        subprocess.run(cmd, cwd=str(ROOT_DIR))
    except KeyboardInterrupt:
        print("\n🛑 Encerrando contêineres do Docker...")
        subprocess.run(["docker", "compose", "down"], cwd=str(ROOT_DIR))
        print("✓ Contêineres finalizados com sucesso.")


def find_python_executable() -> str:
    """Localiza o interpretador Python preferencial (do venv do backend ou global)."""
    if IS_WINDOWS:
        venv_py = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    else:
        venv_py = BACKEND_DIR / ".venv" / "bin" / "python"

    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def find_npm_executable() -> str:
    """Localiza o executável do npm."""
    npm_path = shutil.which("npm.cmd" if IS_WINDOWS else "npm")
    if not npm_path:
        npm_path = "npm"
    return npm_path


def pipe_output(proc: subprocess.Popen, prefix: str, color_code: str):
    """Lê a saída do subprocesso e imprime com prefixo formatado."""
    reset = "\033[0m" if not IS_WINDOWS or "WT_SESSION" in os.environ else ""
    color = color_code if not IS_WINDOWS or "WT_SESSION" in os.environ else ""

    try:
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            text = line.rstrip()
            if text:
                print(f"{color}[{prefix}]{reset} {text}", flush=True)
    except Exception:
        pass


def kill_proc_tree(proc: subprocess.Popen):
    """Mata o processo e toda a sua árvore de filhos."""
    if proc.poll() is not None:
        return
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def cleanup():
    """Finaliza todos os processos filhos ao sair."""
    global TERMINATING
    if TERMINATING:
        return
    TERMINATING = True
    print("\n🛑 Encerrando todos os serviços do Organizer App...")
    for proc in CHILD_PROCESSES:
        kill_proc_tree(proc)
    print("✓ Todos os serviços foram finalizados. Até logo!")


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    """Aguarda até que a porta local comece a responder."""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.3)
    return False


def run_native():
    """Inicia todos os serviços concorrentemente de forma nativa."""
    python_exe = find_python_executable()
    npm_exe = find_npm_executable()

    print("\n" + "=" * 75)
    print("🚀 INICIANDO ORGANIZER APP — MODO NATIVO (COMANDO ÚNICO)")
    print("=" * 75)
    print(f"• Python:   {python_exe}")
    print(f"• npm:      {npm_exe}")
    print(f"• Raiz:     {ROOT_DIR}")
    print("=" * 75 + "\n")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 1. Inicia o Backend FastAPI (Porta 8000)
    print("⏳ [1/3] Inicializando Backend FastAPI (porta 8000)...")
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]
    proc_backend = subprocess.Popen(
        backend_cmd,
        cwd=str(BACKEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    CHILD_PROCESSES.append(proc_backend)
    t_back = threading.Thread(
        target=pipe_output, args=(proc_backend, "BACKEND", "\033[94m"), daemon=True
    )
    t_back.start()

    # 2. Inicia o Frontend React / Vite (Porta 5173)
    print("⏳ [2/3] Inicializando Frontend React (porta 5173)...")
    frontend_cmd = [npm_exe, "run", "dev"]
    proc_frontend = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=IS_WINDOWS,
    )
    CHILD_PROCESSES.append(proc_frontend)
    t_front = threading.Thread(
        target=pipe_output, args=(proc_frontend, "FRONTEND", "\033[92m"), daemon=True
    )
    t_front.start()

    # 3. Inicia o Suplemento Microsoft Excel Add-in (Porta 3000)
    print("⏳ [3/3] Inicializando Servidor do Suplemento Excel (porta 3000)...")
    addin_cmd = [python_exe, "serve.py"]
    proc_addin = subprocess.Popen(
        addin_cmd,
        cwd=str(ADDIN_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    CHILD_PROCESSES.append(proc_addin)
    t_addin = threading.Thread(
        target=pipe_output, args=(proc_addin, "EXCEL-ADDIN", "\033[93m"), daemon=True
    )
    t_addin.start()

    # Aguarda prontidão das portas
    print("\nVerificando saúde dos serviços...")
    b_ok = wait_for_port(8000, timeout=10)
    f_ok = wait_for_port(5173, timeout=10)
    a_ok = wait_for_port(3000, timeout=10)

    # Dashboard de Acesso
    print("\n" + "=" * 75)
    print("🎉 TODOS OS SERVIÇOS DO ORGANIZER APP ESTÃO EM EXECUÇÃO!")
    print("=" * 75)
    print("🌐 1. Aplicação Web Principal (Frontend):")
    print("   👉 http://localhost:5173")
    print("\n⚡ 2. Backend REST API & Documentação Interativa:")
    print("   👉 Swagger UI: http://localhost:8000/api/docs")
    print("   👉 ReDoc:      http://localhost:8000/api/redoc")
    print("   👉 Health:     http://localhost:8000/api/health")
    print("\n📊 3. Suplemento Microsoft Excel Add-in:")
    print("   👉 Taskpane Web / Emulador:  https://localhost:3000/src/taskpane.html")
    print("   👉 Manifesto XML:            https://localhost:3000/manifest.xml")
    print("   👉 Fallback HTTP:            http://localhost:3000/src/taskpane.html")
    print("=" * 75)
    print("🛑 Pressione Ctrl+C a qualquer momento para encerrar todos os serviços.\n")

    try:
        # Loop principal monitorando os processos
        while True:
            for p in CHILD_PROCESSES:
                if p.poll() is not None:
                    # Se algum processo morrer inesperadamente
                    pass
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


def main():
    if "--docker" in sys.argv:
        run_with_docker()
    else:
        run_native()


if __name__ == "__main__":
    main()
