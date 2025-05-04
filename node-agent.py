#!/usr/bin/env python3
from lib.regexp import RegExpBuffer
import lib.port as Port
import lib.vardir as Vardir
from os import getenv
from socket import setdefaulttimeout
import json
import time
from lib.promise import Promise
from lib.address import address
import lib.dotenv as dotenv
import re
from lib.server import listen
from lib.fetch import fetch, fetch_sync
from lib.cancellable import Cancellable
from lib.shmem_msg import MessageRegion

DELAY_A = 0.1
setdefaulttimeout(DELAY_A)

def peer_connect(address):
  pass

def get_this_address():
  return "127.0.0.1"

def work_submit_info():
  def on_response(response):
    print(f"agent: tracker responsed: \"{response}\"")
  body = {
    "stable_port": Port.get(),
  }
  print(f"agent: submitting info to tracker")
  return fetch(TRACKER_ADDRESS, "submit_info", body).then(on_response)

def on_connection(request, response):
  pass

def login_async(username, password):
  global USER
  def a(username, password, _):
    global USER
    USER = f"{username}:{password}"
  return Promise(target=a, args=[username, password])

aa = re.compile(r"^connect:([\\.0-9]+):([0-9]+)$")
ab = re.compile(r"^exit$")
ac = re.compile(r"^print_info$")
ad = re.compile(r"^submit_info$")
ae = re.compile(r"^login:([^:]+):([^:]+)$")

def on_controller_message(message, cancellable):
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
    print(f"address: {get_this_address()}:{lib.port.get()}")
    return
  elif regexp.match(ad, message):
    work_submit_info().start()
    return
  elif regexp.match(ae, message):
    username = regexp.group(1)
    password = regexp.group(2)
    login_async(username, password).start()
    return
  print(f"cli-message: unknown message \"{message}\"")

USER = None

def on_debug_auth_change(user):
  if user is None:
    print("auth: not logged in")
  else:
    print(f"auth: logged in {user}")

def work_watch_auth(cancellable, on_change):
  prev_user = "unset"
  while cancellable.is_set():
    if USER == prev_user: continue
    on_change(USER)
    prev_user = USER
  pass

PEER_LIST = None

def work_autofetch_peer_list(cancellable, on_received_new_peer_list):
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

def on_received_new_peer_list(peer_list):
  print(f"new list {json.dumps(peer_list)}")

if __name__ == "__main__":
  dotenv.source(prefix="node-agent")
  global TRACKER_ADDRESS
  TRACKER_ADDRESS = address(getenv("TRACKER_ADDRESS"))
  cancellable = Cancellable()
  # setup inter-process server
  msg_region = Vardir.path(f"node_agent-{Port.get()}/in")
  msg_region = MessageRegion(msg_region)
  msg_region.start(on_controller_message, cancellable)
  # setup inter-network server
  nodeaddr = get_this_address(), Port.get()
  listen(nodeaddr, on_connection, cancellable).start()
  # watch auth
  Promise(target=work_watch_auth, args=[cancellable]).then(on_debug_auth_change).start()
  # autofetch peer list
  Promise(target=work_autofetch_peer_list, args=[cancellable]).then(on_received_new_peer_list).start()
