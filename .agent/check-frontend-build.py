"""Run the frontend gates, preserving only Next's generated type-reference file."""
import pathlib
import subprocess
import sys

path = pathlib.Path('frontend/next-env.d.ts')
original = path.read_bytes()
status = 0
try:
    for gate in ('build', 'lint', 'typecheck'):
        status = subprocess.run(['npm', '--prefix', 'frontend', 'run', gate]).returncode
        if status:
            break
finally:
    path.write_bytes(original)
sys.exit(status)
