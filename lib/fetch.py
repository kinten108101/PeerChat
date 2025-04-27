from lib.promise import Promise
from socket import socket as make_socket
import json
from threading import Thread
from threading import Event

def work_fetch(host, port, id, body, on_response):
  body = json.dumps(body)
  content = f"{id}:{body}"
  print(f"fetch: sending \"{content}\"")
  socket = make_socket()
  socket.connect((host, port))
  content = content.encode()
  socket.sendall(content)
  response = socket.recv(1024)
  response = response.decode()
  on_response(response)

def fetch(address, id, body):
  """ to fetch is to establish a one-time connection where a request is sent and a response is received. This is mostly inspired by the fetch function from NodeJS and browser JavaScript """
  host, port = address
  return Promise(target=work_fetch, args=(host, port, id, body))
