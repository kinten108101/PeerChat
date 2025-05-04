#!/usr/bin/env python3
import sys
import os
import time
import re
import socket
import json
from datetime import datetime
from pathlib import Path

_stdlib_print = print

LOG_DIR = "var"
os.makedirs(LOG_DIR, exist_ok=True)

class Logger:
    def __init__(self, domain, port=None, session_id=None):
        """
        Initialize logger with domain and optional port or session_id
        - domain: Component name 
        - port: Port number
        - session_id: Session ID 
        """
        self.domain = domain
        self.port = port
        self.session_id = session_id
        
        # Determine log file path based on application tier
        if port is not None:  # Back-end component
            self.log_path = os.path.join(LOG_DIR, f"{port}")
            self.header = f"{domain}/{port}"
        elif session_id is not None:  # Front-end component
            self.log_path = os.path.join(LOG_DIR, f"gui-session-{session_id}")
            self.header = f"{domain}"
        else:
            self.log_path = os.path.join(LOG_DIR, f"{domain}")
            self.header = f"{domain}"
            
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {self.header}: {message}\n"
        
        with open(self.log_path, "a") as f:
            f.write(log_entry)
        
        _stdlib_print(log_entry.strip(), file=sys.stderr)
    
    def chat_message(self, sender, receiver, message):
        chat_data = {
            "type": "chat",
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "timestamp": time.time()
        }
        self.log(f"CHAT: {json.dumps(chat_data)}")
    
    def file_transfer(self, sender, receiver, filename, size, status):
        file_data = {
            "type": "file",
            "sender": sender,
            "receiver": receiver,
            "filename": filename,
            "size": size,
            "status": status,
            "timestamp": time.time()
        }
        self.log(f"FILE: {json.dumps(file_data)}")
    
    def connection(self, peer, status):
        conn_data = {
            "type": "connection",
            "peer": peer,
            "status": status,
            "timestamp": time.time()
        }
        self.log(f"CONN: {json.dumps(conn_data)}")
    
    def error(self, message, details=None):
        error_data = {
            "type": "error",
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.log(f"ERROR: {json.dumps(error_data)}")

    def system(self, action, details=None):
        system_data = {
            "type": "system",
            "action": action,
            "details": details,
            "timestamp": time.time()
        }
        self.log(f"SYSTEM: {json.dumps(system_data)}")

def create_backend_logger(domain, port):
    return Logger(domain, port=port)

def create_frontend_logger(session_id):
    return Logger("gui", session_id=session_id)

def print(s):
    _stdlib_print(f"app: {s}", file=sys.stderr)
    
    try:
        port = os.getenv("PORT")
        if port:
            log_path = os.path.join(LOG_DIR, f"{port}")
            with open(log_path, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                f.write(f"[{timestamp}] app: {s}\n")
    except Exception:
        try:
            general_log = os.path.join(LOG_DIR, "general.log")
            with open(general_log, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                f.write(f"[{timestamp}] app: {s}\n")
        except Exception:
            pass