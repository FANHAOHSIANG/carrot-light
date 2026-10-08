"""Desktop network test; deliberately not connected to vehicle inputs."""
import argparse
import socket
import time
from ambientd import encode
p=argparse.ArgumentParser()
p.add_argument('--ip',required=True)
p.add_argument('--port',type=int,default=7799)
p.add_argument('--token',type=int,default=324508639)
a=p.parse_args()
sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
seq=0
for name,flags in [('ambient',128),('left',129),('right',130),('brake',132),('left blindspot',136),('left + blindspot',137),('invalid',0)]:
  print(name,flush=True)
  for _ in range(40):
    sock.sendto(encode(flags,seq,a.token),(a.ip,a.port))
    seq+=1
    time.sleep(0.05)
print('Stopped. ESP32 must clear valid/warnings within 500ms.')
