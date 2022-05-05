
import time
import socket
import base64

src     = '192.168.1.2'       # ip of remote
mac     = '00-AB-11-11-11-11' # mac of remote
remote  = 'python remote'     # remote name
dst     = '192.168.1.3'       # ip of tv
app     = 'python'            # iphone..iapp.samsung
tv      = 'LE32C650'          # iphone.LE32C650.iapp.samsung

def push(key):
  new = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  new.connect((dst, 55000))
  msg = chr(0x64) + chr(0x00) +\
        chr(len(base64.b64encode(src)))    + chr(0x00) + base64.b64encode(src) +\
        chr(len(base64.b64encode(mac)))    + chr(0x00) + base64.b64encode(mac) +\
        chr(len(base64.b64encode(remote))) + chr(0x00) + base64.b64encode(remote)
  pkt = chr(0x00) +\
        chr(len(app)) + chr(0x00) + app +\
        chr(len(msg)) + chr(0x00) + msg
  new.send(pkt)
  msg = chr(0x00) + chr(0x00) + chr(0x00) +\
        chr(len(base64.b64encode(key))) + chr(0x00) + base64.b64encode(key)
  pkt = chr(0x00) +\
        chr(len(tv))  + chr(0x00) + tv +\
        chr(len(msg)) + chr(0x00) + msg
  new.send(pkt)
  new.close()
  time.sleep(0.1)
  
while True:
  # switch to tv
  push("KEY_TV")
  
  # switch to channel one
  push("KEY_1")
  push("KEY_ENTER")
  
  time.sleep(5)
  
  # switch to channel 15
  push("KEY_1")
  push("KEY_5")
  push("KEY_ENTER")
  
  time.sleep(5)
  
  # switch to HDMI
  push("KEY_HDMI")
  
  time.sleep(5)
