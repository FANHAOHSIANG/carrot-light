"""Run parked/offroad. Requires explicit --root; reversible exact-line patch."""
import argparse
import ast
import shutil
from pathlib import Path

LINE = '  PythonProcess("ambient_light", "openpilot.selfdrive.carrot.ambientd", only_onroad, restart_if_crash=True, spawn=True),\n'
p = argparse.ArgumentParser()
p.add_argument('--root', type=Path, required=True)
p.add_argument('--uninstall', action='store_true')
a = p.parse_args()
root = a.root.resolve()
manager = root / 'openpilot/system/manager/process_config.py'
dest = root / 'openpilot/selfdrive/carrot/ambientd.py'
text = manager.read_text()
backup = manager.with_name('process_config.py.ambient-backup')
if a.uninstall:
  updated = text.replace(LINE, '')
  ast.parse(updated)
  manager.write_text(updated)
  # Keep module/config: safe removal from manager avoids deleting later edits.
  print('Automatic startup removed. Module and config retained. Restart offroad.')
else:
  if 'def only_onroad(' not in text or 'procs = [\n' not in text:
    raise SystemExit('Unsupported manager layout; no edits made.')
  if '"ambient_light"' in text and LINE not in text:
    raise SystemExit('Another ambient_light entry exists; no edits made.')
  if dest.exists() and dest.read_bytes() != (Path(__file__).parent/'ambientd.py').read_bytes():
    raise SystemExit('Existing ambientd.py differs; back it up/remove it manually first.')
  updated = text if LINE in text else text.replace('procs = [\n', 'procs = [\n'+LINE, 1)
  ast.parse(updated)
  if not backup.exists():
    shutil.copy2(manager, backup)
  shutil.copy2(Path(__file__).parent/'ambientd.py', dest)
  manager.write_text(updated)
  print('Installed. Missing config uses local broadcast; optional config is /data/ambient_light/config.json.')
