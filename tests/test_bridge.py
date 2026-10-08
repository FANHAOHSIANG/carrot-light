import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
import tempfile
import subprocess
import sys
spec = importlib.util.spec_from_file_location('ambientd', Path(__file__).parents[1]/'comma/ambientd.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
class Tests(unittest.TestCase):
  def test_missing_config_uses_local_broadcast(self):
    with tempfile.TemporaryDirectory() as d:
      cfg = m.load_config(Path(d)/'missing.json')
      self.assertEqual(cfg['target_ip'], '255.255.255.255')
      self.assertEqual(cfg['brake_mode'], 'pedal')

  def test_invalid_clears_every_warning(self):
    cs=SimpleNamespace(leftBlinker=True, rightBlinker=True, brakePressed=True, leftBlindspot=True, rightBlindspot=True)
    self.assertEqual(m.flags_for(cs, False), 0)
    self.assertEqual(m.flags_for(cs, True), 159)
  def test_brake_modes_differ_for_regen(self):
    cs=SimpleNamespace(brakePressed=False, brakeLights=True)
    self.assertEqual(m.flags_for(cs, True, 'pedal'), 128)
    self.assertEqual(m.flags_for(cs, True, 'lights'), 132)
  def test_packet_layout_and_wrap(self):
    self.assertEqual(m.encode(145, 2**32+7, 324508639).hex(), '414c3031019100000000000713579bdf')
  def test_install_reversible_and_repeatable(self):
    with tempfile.TemporaryDirectory() as d:
      root=Path(d)
      manager=root/'openpilot/system/manager/process_config.py'
      manager.parent.mkdir(parents=True)
      (root/'openpilot/selfdrive/carrot').mkdir(parents=True)
      original='def only_onroad(*args): return True\nprocs = [\n]\n'
      manager.write_text(original)
      cmd=[sys.executable,str(Path(__file__).parents[1]/'comma/install.py'),'--root', d]
      subprocess.run(cmd,check=True,capture_output=True)
      subprocess.run(cmd,check=True,capture_output=True)
      self.assertEqual(manager.read_text().count('PythonProcess('),1)
      # Uninstall preserves unrelated updates after installation.
      manager.write_text(manager.read_text()+'# later update\n')
      subprocess.run(cmd+['--uninstall'],check=True,capture_output=True)
      self.assertEqual(manager.read_text(),original+'# later update\n')
if __name__=='__main__': unittest.main()
