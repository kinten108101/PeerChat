#!/usr/bin/env python3
from lib.regexp import RegExpBuffer
import lib.port as Port
import lib.vardir as Vardir
from os import getenv
from socket import setdefaulttimeout
from lib.address import address
import lib.dotenv as dotenv
import re
from lib.server import listen
from lib.fetch import fetch
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

aa = re.compile(r"^connect:([\\.0-9]+):([0-9]+)$")
ab = re.compile(r"^exit$")
ac = re.compile(r"^print_info$")
ad = re.compile(r"^submit_info$")

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
  print(f"cli-message: unknown message \"{message}\"")

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
  listen(nodeaddr, on_connection, cancellable)
