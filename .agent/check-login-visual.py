"""Run root-owned browser checks on a temporary loopback port; restore generated types."""
import os
import pathlib
import signal
import socket
import subprocess
import sys
import time
import urllib.request

root = pathlib.Path.cwd()
tag = sys.argv[1]
args = sys.argv[2:] or ["e2e/accessibility.spec.ts", "--workers=2"]
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
env = os.environ.copy()
env.pop("CI", None)
env.update(PLAYWRIGHT_PORT=str(port), NEXT_PUBLIC_API_URL="http://localhost:18000",
           TEST_BASE_URL=f"http://localhost:{port}")
path = root / "frontend/next-env.d.ts"
original = path.read_bytes()
status = 1
with open(f".agent/results/{tag}.server.raw.log", "w") as log:
    process = subprocess.Popen(["npm", "--prefix", "frontend", "run", "dev", "--",
                                "--hostname", "127.0.0.1", "--port", str(port)],
                               env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        for attempt in range(120):
            if process.poll() is not None:
                raise RuntimeError("temporary server exited")
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/login", timeout=3).close()
                break
            except Exception:
                time.sleep(1)
        else:
            raise RuntimeError("temporary server did not become ready")
        status = subprocess.run(["node", ".agent/results/T-44283.inspect.raw.mjs"], env=env).returncode
        if not status:
            status = subprocess.run(["npx", "--no-install", "playwright", "test", *args],
                                    cwd=root / "frontend", env=env).returncode
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        path.write_bytes(original)
sys.exit(status)
