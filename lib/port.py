from socket import socket as Socket
import socket

def is_port_in_use(port):
  with Socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    return s.connect_ex(('localhost', port)) == 0

def generate():
  port = 2000
  port = int(port)
  while is_port_in_use(port):
    port = port + 1
  return port

_PORT = None

def get():
  global _PORT
  if _PORT is None:
    _PORT = generate()
  return _PORT
