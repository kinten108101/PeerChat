#!/usr/bin/env python3
from lib.fetch import fetch

TRACKER_ADDRESS = ("127.0.0.1", 7090)

def peer_connect(address):
  pass

def submit_info():
  def on_response(response):
    print(f"agent: tracker responsed: \"{response}\"")
  body = {}
  body["address"] = ("127.0.0.1", 723)
  print(f"agent: submitting info to tracker")
  fetch(TRACKER_ADDRESS, "submit_info", body, on_response)

submit_info()
