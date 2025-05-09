#!/usr/bin/env python3
from lib.regexp import RegExpBuffer
from lib.port import Port
from lib.vardir import Vardir
import os
from socket import setdefaulttimeout
import json
import time
from lib.promise import Promise
from lib.address import address
import lib.dotenv
import re
from lib.server import Server
from lib.fetch import fetch, fetch_sync
from lib.cancellable import Cancellable
from lib.shmem_msg import InputMessageRegion, OutputMessageRegion
from lib.logging import print

DELAY_A = 1
setdefaulttimeout(DELAY_A)

def peer_connect(address):
  pass

def get_this_address():
  return "127.0.0.1"

def submit_info_async():
  def on_response(response):
    print(f'agent: tracker responsed: \"{response}\"')
  body = {
    "stable_port": Port.get(),
  }
  print(f"agent: submitting info to tracker")
  return fetch(TRACKER_ADDRESS, "submit_info", body).then(on_response)

re_check_alive = re.compile(r"^check_alive:{}$")
re_message_raw = re.compile(r'^send_message_raw:(.+)$')

def on_connection(request, response, writer):
  regexp = RegExpBuffer()
  if regexp.match(re_check_alive, request.message):
    response.write("is_alive:{}")
  elif regexp.match(re_message_raw, request.message):
    body = regexp.group(1)
    body = json.loads(body)
    content = f'connection: received message: {body["message"]}'
    print(content)
    writer.write(content)
  response.close()

def login_async(username, password):
  global USER
  def a(username, password, _):
    global USER
    USER = f"{username}:{password}"
  return Promise(target=a, args=[username, password])

def get_list_async():
  return fetch(TRACKER_ADDRESS, "get_list", {})

def send_message_raw_async(address, message):
  return fetch(address, "send_message_raw", { "message": message })

aa = re.compile(r'^connect:{ "address": "([\\.0-9]+):([0-9]+)" }$')
ab = re.compile(r"^exit:{}$")
ac = re.compile(r"^print_info:{}$")
ad = re.compile(r"^submit_info:{}$")
ae = re.compile(r'^login:{ "name": "([^:]+)", "password": "([^:]+)" }$')
af = re.compile(r'^send_message_raw:{ "node_address": "(.+)", "message": "(.+)" }$')
ak = re.compile(r'^get_list:{}$')

def on_controller_message(message, cancellable, writer):
  regexp = RegExpBuffer()
  if regexp.match(aa, message):
    print("connecting..." + regexp.group(1) + " " + regexp.group(2))
    host = regexp.group(1)
    port = regexp.group(2)
    port = int(port)
    def ondone(): pass
    fetch(host, port, ondone)
    return
  elif regexp.match(ab, message):
    print("exiting")
    cancellable.clear()
    return
  elif regexp.match(ac, message):
    content = f"address: {get_this_address()}:{Port.get()}"
    print(content)
    writer.write(content)
    return
  elif regexp.match(ad, message):
    submit_info_async().start()
    return
  elif regexp.match(ae, message):
    username = regexp.group(1)
    password = regexp.group(2)
    login_async(username, password).start()
    return
  elif regexp.match(af, message):
    node_address = regexp.group(1)
    content = regexp.group(2)
    def then(response):
      print("message sent")
    send_message_raw_async(node_address, content).then(then).start()
    return
  elif regexp.match(ak, message):
    def then(response):
      message = f"get_list: current list is {response}"
      print(message)
      writer.write(message)
    get_list_async().then(then).start()
  print(f'cli-message: unknown message \"{message}\"')

USER = None

def watch_auth_async(cancellable):
  def target(on_change):
    prev_user = "unset"
    while cancellable.is_set():
      if USER == prev_user: continue
      on_change(USER)
      prev_user = USER
    pass
  return Promise(target=target, args=[])

def on_debug_auth_change(user):
  if user is None:
    print("auth: not logged in")
  else:
    print(f"auth: logged in {user}")

PEER_LIST = None

def autofetch_peer_list_async(cancellable):
  def target(on_received_new_peer_list):
    global PEER_LIST
    prev_list = {}
    # In a production environment, it's the server notifying the client
    # Here, the client is fetching for event (peer list change) from the server
    # It's an antipattern
    while cancellable.is_set():
      try:
        x = fetch_sync(TRACKER_ADDRESS, "get_list", {})
        x = json.loads(x)
        if x != prev_list:
          on_received_new_peer_list(x)
        PEER_LIST = x
        prev_list = PEER_LIST
        time.sleep(1)
      except ConnectionRefusedError:
        print("could not connect to tracker, retrying (1s)")
        time.sleep(1)
  return Promise(target=target, args=[])

def on_received_new_peer_list(peer_list):
  print(f"new list {json.dumps(peer_list)}")

if __name__ == "__main__":
  lib.dotenv.source(prefix="node-agent")
  global TRACKER_ADDRESS
  TRACKER_ADDRESS = address(os.getenv("TRACKER_ADDRESS"))
  cancellable = Cancellable()
  # setup output
  region = Vardir.path(f"node_agent-{Port.get()}", "out")
  writer = OutputMessageRegion(region)
  # setup inter-process server
  msg_region = Vardir.path(f"node_agent-{Port.get()}", "in")
  msg_region = InputMessageRegion(msg_region)
  def _on_controller_message(*args):
    return on_controller_message(*args, writer)
  msg_region.watch_async(cancellable).then(_on_controller_message).start()
  # setup inter-network server
  nodeaddr = get_this_address(), Port.get()
  os.environ["PORT"] = str(Port.get())
  server = Server(nodeaddr)
  def _on_connection(*args):
    return on_connection(*args, writer)
  server.listen_async(cancellable).then(_on_connection).start()
  # autofetchers
  watch_auth_async(cancellable).then(on_debug_auth_change).start()
  autofetch_peer_list_async(cancellable).then(on_received_new_peer_list).start()
  try:
    while True:
      time.sleep(0.1)
  except KeyboardInterrupt:
    cancellable.clear()
