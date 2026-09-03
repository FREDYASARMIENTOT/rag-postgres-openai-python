"""Start FastAPI server in background and save PID for later cleanup."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
log = HERE / "server.log"
pid_file = HERE / "server.pid"

proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "fastapi_app:create_app",
     "--host", "0.0.0.0", "--port", "8000", "--no-access-log"],
    cwd=str(HERE),
    stdout=open(str(log), "w"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
)

pid_file.write_text(str(proc.pid))
print(f"Server started with PID {proc.pid}")
print(f"Log: {log}")
print(f"PID file: {pid_file}")