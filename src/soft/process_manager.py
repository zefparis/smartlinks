import subprocess, threading, collections
import os
from pathlib import Path

# Process registry
PROCESSES = {}
LOGS = {
    "router": collections.deque(maxlen=200),
    "autopilot": collections.deque(maxlen=200),
    "probes": collections.deque(maxlen=200),
}

def _reader(name, pipe):
    """Thread: lit stdout d’un process et stocke dans LOGS[name]"""
    for line in iter(pipe.readline, b""):
        LOGS[name].append(line.decode(errors="ignore").rstrip())
    pipe.close()

def start_service(name: str):
    if name in PROCESSES and PROCESSES[name].poll() is None:
        return False  # déjà en cours

    cmd = None
    if name == "router":
        cmd = ["python", "-m", "soft.router"]
    elif name == "autopilot":
        cmd = ["python", "-m", "soft.autopilot"]
    elif name == "probes":
        cmd = ["python", "-m", "soft.simulate"]

    if not cmd:
        raise ValueError(f"Unknown service: {name}")

    # Ensure 'soft' package is importable when running as module.
    # Our codebase is under '<project_root>/src/soft', so we must add '<project_root>/src' to PYTHONPATH.
    soft_dir = Path(__file__).resolve().parent            # .../src/soft
    src_dir = soft_dir.parent                              # .../src
    project_root = src_dir.parent                          # .../
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    # Prepend src_dir to PYTHONPATH if not already present
    py_path = str(src_dir)
    if existing:
        env["PYTHONPATH"] = py_path + os.pathsep + existing
    else:
        env["PYTHONPATH"] = py_path

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        cwd=str(project_root),
        env=env,
    )
    PROCESSES[name] = proc
    LOGS[name].clear()

    # thread pour lire stdout
    threading.Thread(target=_reader, args=(name, proc.stdout), daemon=True).start()
    return True

def stop_service(name: str):
    proc = PROCESSES.get(name)
    if proc and proc.poll() is None:
        proc.terminate()
        return True
    return False

def get_logs(name: str) -> str:
    return "\n".join(LOGS.get(name, []))
