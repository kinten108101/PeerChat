#!/usr/bin/env python3
from os import getenv
import lib.dotenv as dotenv
from lib.fetch import fetch


def peer_connect(address):
  pass

def work_submit_info():
  def on_response(response):
    print(f"agent: tracker responsed: \"{response}\"")
  body = {}
  body["address"] = ("127.0.0.1", 723)
  print(f"agent: submitting info to tracker")
  return fetch(TRACKER_ADDRESS, "submit_info", body).then(on_response)

if __name__ == "__main__":
  dotenv.source(prefix="node-agent")
  trackaddr = getenv("TRACKER_ADDRESS")
  if trackaddr is None:
    raise Exception("wtf")
  trackaddr = trackaddr.split(":")
  global TRACKER_ADDRESS
  TRACKER_ADDRESS = trackaddr[0], int(trackaddr[1])
  work_submit_info().start()
