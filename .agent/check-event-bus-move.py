"""Verify the EventBus extraction is an exact class-body move."""
import ast
import pathlib
import subprocess
import sys

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
base = "62443d007a6eff33986ae68ee9f7e4177685104c"
original = ast.parse(subprocess.check_output(['git','show',base+':backend/app/main.py'],text=True))
current = ast.parse(pathlib.Path('backend/app/core/events.py').read_text())
old_class = next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='EventBus')
new_class = next(n for n in current.body if isinstance(n,ast.ClassDef) and n.name=='EventBus')
assert ast.dump(old_class)==ast.dump(new_class)
assert not any(isinstance(n,ast.ClassDef) and n.name=='EventBus' for n in ast.parse(pathlib.Path('backend/app/main.py').read_text()).body)
from backend.app import main
from backend.app.core.events import EventBus
assert main.EventBus is EventBus and type(main.bus) is EventBus
print('PASS EventBus body AST identical; main public alias and singleton retained')
