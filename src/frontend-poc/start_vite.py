"""Start Vite dev server in background and save PID."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
log = HERE / "vite.log"
pid_file = HERE / "vite.pid"

proc = subprocess.Popen(
    ["npx", "vite", "--port", "5173", "--host", "0.0.0.0"],
    cwd=str(HERE),
    stdout=open(str(log), "w"),
    stderr=subprocess.STDOUT,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    shell=True,
)

pid_file.write_text(str(proc.pid))
print(f"Vite started with PID {proc.pid}")
print(f"Log: {log}")
print(f"PID file: {pid_file}")