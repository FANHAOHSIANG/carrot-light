"""Retarget only two reserved fields in comma's AArch64 AGNOS ELF installer."""
import argparse
import hashlib
from pathlib import Path
import struct
p=argparse.ArgumentParser()
p.add_argument('template',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
b=a.template.read_bytes()
assert b[:4]==b'\x7fELF' and b[4:6]==b'\x02\x01', 'Expected 64-bit little endian ELF'
assert struct.unpack_from('<H',b,18)[0]==183, 'Expected AArch64'
updated=b
regions=[]
for old,new in [
 (b'https://github.com/commaai/openpilot.git?',b'https://github.com/FANHAOHSIANG/carrot-light.git?'),
 (b'release3?',b'carrot-wip?'),
]:
 assert updated.count(old)==1, 'Unknown installer field layout'
 offset=updated.index(old)
 end=updated.index(b'\x00',offset)
 field=updated[offset:end]
 assert field[len(old):].strip(b' ')==b'', 'Unknown padding'
 assert len(new)<=len(field), 'Insufficient reserved field space'
 updated=updated[:offset]+new.ljust(len(field),b' ')+updated[end:]
 regions.append((offset,end))
assert len(updated)==len(b)
assert all(any(start<=i<end for start,end in regions) for i,(x,y) in enumerate(zip(b,updated)) if x!=y)
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_bytes(updated)
a.output.chmod(0o755)
print('Template SHA256:',hashlib.sha256(b).hexdigest())
print('Output SHA256:',hashlib.sha256(updated).hexdigest())
print('Changed only reserved repository URL and branch fields.')
