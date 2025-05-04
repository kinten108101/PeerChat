#!/usr/bin/env python3
import os
import json
import hashlib
import time
from pathlib import Path

class UserManager:
    def __init__(self, base_dir="var"):
        self.base_dir = base_dir
        self.users_dir = os.path.join(base_dir, "users")
        self.ensure_dirs_exist()
        self.current_user = None
    
    def ensure_dirs_exist(self):
        os.makedirs(self.users_dir, exist_ok=True)
    
    def user_exists(self, username):
        user_file = os.path.join(self.users_dir, f"{username}.json")
        return os.path.exists(user_file)
    
    def hash_password(self, password):
        salt = "netapp_secure_salt"  # In production
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def register_user(self, username, password, ip, port):
        if self.user_exists(username):
            return False, "Username already exists"
        
        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "ip": ip,
            "port": port,
            "created_at": time.time(),
            "last_login": None
        }
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'w') as f:
            json.dump(user_data, f)
        
        return True, "User registered successfully"
    
    def authenticate(self, username, password):
        if not self.user_exists(username):
            return False, "User does not exist"
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'r') as f:
            user_data = json.load(f)
        
        if user_data["password_hash"] == self.hash_password(password):
            user_data["last_login"] = time.time()
            with open(user_file, 'w') as f:
                json.dump(user_data, f)
            
            self.current_user = user_data
            return True, "Authentication successful"
        
        return False, "Invalid password"
    
    def get_user_info(self, username):
        if not self.user_exists(username):
            return None
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'r') as f:
            return json.load(f)
    
    def update_user_address(self, username, ip, port):
        if not self.user_exists(username):
            return False, "User does not exist"
        
        user_data = self.get_user_info(username)
        user_data["ip"] = ip
        user_data["port"] = port
        
        user_file = os.path.join(self.users_dir, f"{username}.json")
        with open(user_file, 'w') as f:
            json.dump(user_data, f)
        
        if self.current_user and self.current_user["username"] == username:
            self.current_user = user_data
        
        return True, "User address updated"
    
    def get_current_user(self):
        return self.current_user
    
    def logout(self):
        self.current_user = None
        return True, "Logged out successfully"
    
    def get_all_users(self):
        users = []
        for filename in os.listdir(self.users_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.users_dir, filename), 'r') as f:
                    user_data = json.load(f)
                    users.append({
                        "username": user_data["username"],
                        "ip": user_data["ip"],
                        "port": user_data["port"],
                        "last_login": user_data["last_login"]
                    })
        return users