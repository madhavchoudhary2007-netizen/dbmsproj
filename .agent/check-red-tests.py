"""Record an intentional test-first failure; never call failing product assertions green."""
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

task, *files = sys.argv[1:]
assert files
output = pathlib.Path('.agent/results')
output.mkdir(parents=True, exist_ok=True)
report = output / (task + '.red.raw.xml')
log = output / (task + '.red.raw.log')
env = dict(os.environ, APP_ENV='local', PYTHONPATH='backend',
           DATABASE_URL='postgresql://invalid:invalid@127.0.0.1:1/never_connect',
           MONGODB_URL='mongodb://127.0.0.1:1')
r = subprocess.run(['.venv/bin/pytest', '-q', '--tb=short', '--junitxml=' + str(report), *files],
                   env=env, text=True, capture_output=True)
log.write_text(r.stdout + r.stderr)
root = ET.parse(report).getroot()
cases = list(root.iter('testcase'))
failed = [c for c in cases if c.find('failure') is not None]
errors = [c for c in cases if c.find('error') is not None]
skipped = [c for c in cases if c.find('skipped') is not None]
print(f'EXPECTED RED BASELINE: pytest_exit={r.returncode} collected={len(cases)} '
      f'passed={len(cases)-len(failed)-len(errors)-len(skipped)} failed={len(failed)} '
      f'errors={len(errors)} skipped={len(skipped)}')
for c in failed:
    print('FAILURE:', c.attrib.get('name', '?'))
assert r.returncode == 1 and cases and failed and not errors and not skipped, 'not a clean intentional red baseline'
for c in failed:
    failure = c.find('failure')
    text = (failure.text or '') if failure is not None else ''
    assert 'AssertionError' in text or 'Failed:' in text, 'unexpected runtime/import failure'
print('Recorded missing-feature assertions; no product check marked passed.')
