#!/usr/bin/env python3
from socket import setdefaulttimeout
from lib.shmem_msg import InputMessageRegion
from lib.port import Port
from lib.vardir import Vardir
import re
import time
import os
import json
import lib.dotenv
from lib.cancellable import Cancellable
from lib.address import address
from lib.server import Server
from lib.regexp import RegExpBuffer
from threading import Lock
import socket
from lib.promise import Promise

DELAY_A = 1
setdefaulttimeout(DELAY_A)

mutex = Lock()

TRACKING = {}  #

def add_list(body, ip):
  global TRACKING, mutex
  with mutex:
    TRACKING[f'{ip}:{body["stable_port"]}'] = "test"

def get_list():
  return json.dumps(TRACKING)

re_submit_info = re.compile(r"^submit_info:(.+)$")
re_get_list = re.compile(r"^get_list:{}$")

def on_connection(request, response):
  print(f'tracker: received from client: \"{request.message}\"')
  regexp = RegExpBuffer()
  if regexp.match(re_submit_info, request.message):
    print(f"tracker: request is submit_info")
    body = regexp.group(1)
    body = json.loads(body)
    ip = request.address[0]
    print(f'tracker: submit_info: address {ip}:{body["stable_port"]}')
    add_list(body, ip)
    response.write(get_list())
  elif regexp.match(re_get_list, request.message):
    print(f"tracker: request is get_list")
    response.write(get_list())
  else:
    raise OSError("wtf")
  response.close()

ab = re.compile(r"^exit$")
ae = re.compile(r"^get_list$")

def on_controller_message(message, cancellable):
  regexp = RegExpBuffer()
  if regexp.match(ab, message):
    print("exiting")
    cancellable.clear()
  elif regexp.match(ae, message):
    content = get_list()
    print(f"get_list: list is {content}")
  else:
    OSError(f"cli-message: unknown message \"{message}\"")

def auto_check(cancellable):
  def target(f):
    while cancellable.is_set():
      for client in TRACKING:
        client_socket = socket.socket()
        client_socket.settimeout(5)
        client_ip, client_port = client.split(":")
        try:   
          client_socket.connect((client_ip,int(client_port)))
          check_data = "check_alive:{}"
          client_socket.sendall(f"{check_data}".encode())
          response = client_socket.recv(1024).decode()
          
          if response == "is_alive:{}":
            print(f"Node {client} is online")

          client_socket.close()
        except Exception as e:
          print(f"A node has gone offline {client}")
          print(f"reason: {e}")
          f(client)
          break
      time.sleep(10)
  return Promise(target=target, args=[])
                
def handle_not_alive_client(delete_client):
  global TRACKING
  with mutex:
    if delete_client in TRACKING:
      del TRACKING[delete_client]
          
if __name__ == "__main__":
  lib.dotenv.source(prefix="tracker")
  global ADDRESS
  ADDRESS = address(os.getenv("ADDRESS"))
  cancellable = Cancellable()
  # setup inter-process server
  msg_region = Vardir.path("tracker", "in")
  msg_region = InputMessageRegion(msg_region)
  msg_region.watch_async(cancellable).then(on_controller_message).start()
  # setup inter-network server
  server = Server(ADDRESS)
  server.listen_async(cancellable).then(on_connection).start()
  auto_check(cancellable).then(handle_not_alive_client).start()
  try:
    while True:
      time.sleep(0.1)
  except KeyboardInterrupt:
    cancellable.clear()
