#!/usr/bin/env python3
import os
import json
import time
import base64
import hashlib
import threading
from pathlib import Path

class NodeController:
    """
    Controller class for interacting with node-agent processes for front-end use, referencing shared memory library from shmem.
    """
    
    def __init__(self):
        self.app_dir = os.getcwd()
        self.nodes_dir = os.path.join(self.app_dir, "_nodes")
        os.makedirs(self.nodes_dir, exist_ok=True)
        self.responses = {}
        self.lock = threading.Lock()
    
    def _format_node_address(self, node_address):
        return node_address.replace(':', '_')
    
    def _write_to_node(self, node_address, message):
        safe_address = self._format_node_address(node_address)
        in_file = os.path.join(self.nodes_dir, f"{safe_address}.in")
        
        with open(in_file, 'w') as f:
            f.write(message)
        
        return True
    
    def _read_from_node(self, node_address):
        safe_address = self._format_node_address(node_address)
        out_file = os.path.join(self.nodes_dir, f"{safe_address}.out")
        
        if not os.path.exists(out_file):
            return None
        
        with open(out_file, 'r') as f:
            content = f.read().strip()
            
        if content and content != "done":
            with open(out_file, 'w') as f:
                f.write("")
                
            return content
        
        return None
    
    def submit_info(self, node_address):
        return self._write_to_node(node_address, "submit_info")
    
    def peer_connect(self, node_address, peer_address):
        return self._write_to_node(node_address, f"peer_connect:{peer_address}")
    
    def exit_node(self, node_address):
        return self._write_to_node(node_address, "exit")
    
    def send_chat(self, node_address, recipient, message):
        command = f"send_chat:{recipient}:{message}"
        return self._write_to_node(node_address, command)
    
    def send_file(self, node_address, recipient, file_data):
        """Send a file to a recipient through the node
        
        Args:
            node_address: Address of the local node
            recipient: Address of the recipient
            file_data: Dictionary containing file information
        """
        # Convert file_data to JSON string
        file_json = json.dumps(file_data)
        command = f"send_file:{recipient}:{file_json}"
        return self._write_to_node(node_address, command)
    
    def get_response(self, node_address):
        with self.lock:
            response = self._read_from_node(node_address)
            
            if response:
                if node_address not in self.responses:
                    self.responses[node_address] = []
                    
                self.responses[node_address].append({
                    "content": response,
                    "timestamp": time.time()
                })
                
                if len(self.responses[node_address]) > 100:
                    self.responses[node_address] = self.responses[node_address][-100:]
                    
            return response
    
    def get_all_responses(self, node_address):
        with self.lock:
            if node_address in self.responses:
                return self.responses[node_address]
            return []
    
    def clear_responses(self, node_address):
        with self.lock:
            if node_address in self.responses:
                self.responses[node_address] = []