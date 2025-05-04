from socket import socket as Socket
import socket

def is_port_in_use(port):
  """ from somewhere on stackoverflow """
  with Socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    return s.connect_ex(('localhost', port)) == 0

def generate(starting=2000):
  port = starting
  port = int(port)
  while is_port_in_use(port):
    port = port + 1
  return port

class Port():
  _PORT = None

  def get():
    if Port._PORT is None:
      Port._PORT = generate()
    return Port._PORT
