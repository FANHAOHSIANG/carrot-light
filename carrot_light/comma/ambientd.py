"""Read-only carState -> UDP bridge, carrot-wip e74e6938. No CAN TX."""
import json
import os
import socket
import struct
import time
from pathlib import Path

CONFIG = Path('/data/ambient_light/config.json')
PACKET = struct.Struct('!4sBBHII')


def flags_for(cs, healthy, brake_mode='pedal'):
  if not healthy:
    return 0
  flags = 128
  for bit, field in enumerate(('leftBlinker', 'rightBlinker', 'brakePressed' if brake_mode == 'pedal' else 'brakeLights', 'leftBlindspot', 'rightBlindspot')):
    if bool(getattr(cs, field, False)):
      flags |= 1 << bit
  return flags


def encode(flags, seq, token):
  return PACKET.pack(b'AL01', 1, flags, 0, seq & 0xffffffff, token)


def load_config(path=CONFIG):
  cfg = json.loads(path.read_text()) if path.exists() else {
    'target_ip': '255.255.255.255', 'port': 7799,
    'token': 324508639, 'brake_mode': 'pedal',
  }
  socket.inet_pton(socket.AF_INET, cfg['target_ip'])
  if not 1 <= int(cfg['port']) <= 65535:
    raise ValueError('invalid UDP port')
  if cfg.get('brake_mode', 'pedal') not in ('pedal', 'lights'):
    raise ValueError('brake_mode must be pedal or lights')
  if not 1 <= int(cfg['token']) <= 0xffffffff:
    raise ValueError('token must be nonzero uint32')
  return cfg


def main():
  # Import here so packet logic can be tested without device dependencies.
  from openpilot.cereal import messaging
  try:
    cfg = load_config()
  except Exception as exc:
    print(f'ambientd disabled: {exc}', flush=True)
    # Remain idle rather than creating a manager restart loop.
    while True:
      time.sleep(30)
  try:
    os.nice(10)
  except OSError:
    pass
  sm = messaging.SubMaster(['carState'])
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  sock.setblocking(False)
  target = (cfg['target_ip'], int(cfg['port']))
  seq = 0
  print(f'ambientd sending to {target}; brake={cfg.get("brake_mode", "pedal")}', flush=True)
  while True:
    tick = time.monotonic()
    sm.update(0)
    age = time.monotonic() - sm.recv_time['carState']
    cs = sm['carState']
    healthy = sm.seen['carState'] and sm.valid['carState'] and 0 <= age < 0.3 and bool(cs.canValid)
    flags = flags_for(cs, healthy, cfg.get('brake_mode', 'pedal'))
    try:
      sock.sendto(encode(flags, seq, int(cfg['token'])), target)
    except OSError:
      pass  # Lighting network failures must not stop the driving stack.
    seq = (seq + 1) & 0xffffffff
    time.sleep(max(0, 0.05 - (time.monotonic() - tick)))


if __name__ == '__main__':
  main()
