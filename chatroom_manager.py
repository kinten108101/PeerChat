#!/usr/bin/env python3
import os
import json
import time
import uuid
from pathlib import Path

class ChatroomManager:
    def __init__(self, base_dir="var"):
        self.base_dir = base_dir
        self.chatrooms_dir = os.path.join(base_dir, "chatrooms")
        self.ensure_dirs_exist()
    
    def ensure_dirs_exist(self):
        os.makedirs(self.chatrooms_dir, exist_ok=True)
    
    def generate_chatroom_id(self):
        return str(uuid.uuid4())[:8]
    
    def chatroom_exists(self, chatroom_id):
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        return os.path.exists(chatroom_file)
    
    def create_chatroom(self, name, creator, members=None):
        """Create a new chatroom
        
        Args:
            name: Name of the chatroom
            creator: Username of the creator
            members: List of initial members (usernames)
            
        Returns:
            (success, message, chatroom_id)
        """
        if members is None:
            members = []
            
        if creator not in members:
            members.append(creator)
        
        chatroom_id = self.generate_chatroom_id()
        
        chatroom_data = {
            "id": chatroom_id,
            "name": name,
            "creator": creator,
            "created_at": time.time(),
            "members": members,
            "messages": []
        }
        
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        with open(chatroom_file, 'w') as f:
            json.dump(chatroom_data, f)
        
        messages_dir = os.path.join(self.chatrooms_dir, chatroom_id)
        os.makedirs(messages_dir, exist_ok=True)
        
        return True, "Chatroom created successfully", chatroom_id
    
    def get_chatroom(self, chatroom_id):
        if not self.chatroom_exists(chatroom_id):
            return None
        
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        with open(chatroom_file, 'r') as f:
            return json.load(f)
    
    def add_member(self, chatroom_id, username):
        if not self.chatroom_exists(chatroom_id):
            return False, "Chatroom does not exist"
        
        chatroom_data = self.get_chatroom(chatroom_id)
        if username in chatroom_data["members"]:
            return False, "User already a member"
        
        chatroom_data["members"].append(username)
        
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        with open(chatroom_file, 'w') as f:
            json.dump(chatroom_data, f)
        
        return True, "Member added successfully"
    
    def remove_member(self, chatroom_id, username):
        if not self.chatroom_exists(chatroom_id):
            return False, "Chatroom does not exist"
        
        chatroom_data = self.get_chatroom(chatroom_id)
        if username not in chatroom_data["members"]:
            return False, "User is not a member"
        
        if username == chatroom_data["creator"]:
            return False, "Cannot remove the creator of the chatroom"
        
        chatroom_data["members"].remove(username)
        
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        with open(chatroom_file, 'w') as f:
            json.dump(chatroom_data, f)
        
        return True, "Member removed successfully"
    
    def add_message(self, chatroom_id, sender, content, message_type="text", file_info=None):
        """Add a message to chatroom
        
        Args:
            chatroom_id: ID of the chatroom
            sender: Username of the sender
            content: Text content or file path
            message_type: "text" or "file"
            file_info: Dictionary with file metadata (for file messages)
            
        Returns:
            (success, message)
        """
        if not self.chatroom_exists(chatroom_id):
            return False, "Chatroom does not exist"
        
        chatroom_data = self.get_chatroom(chatroom_id)
        
        if sender not in chatroom_data["members"]:
            return False, "Only members can send messages"
        
        message_data = {
            "id": str(uuid.uuid4()),
            "sender": sender,
            "content": content,
            "type": message_type,
            "timestamp": time.time()
        }
        
        if message_type == "file" and file_info:
            message_data["file_info"] = file_info
        
        chatroom_data["messages"].append(message_data)
        
        chatroom_file = os.path.join(self.chatrooms_dir, f"{chatroom_id}.json")
        with open(chatroom_file, 'w') as f:
            json.dump(chatroom_data, f)
        
        return True, "Message added successfully", message_data
    
    def get_messages(self, chatroom_id, limit=50, before_timestamp=None):
        """Get messages from chatroom
        
        Args:
            chatroom_id: ID of the chatroom
            limit: Maximum number of messages to return
            before_timestamp: Only return messages before this timestamp
            
        Returns:
            List of messages
        """
        if not self.chatroom_exists(chatroom_id):
            return []
        
        chatroom_data = self.get_chatroom(chatroom_id)
        messages = chatroom_data["messages"]
        
        if before_timestamp:
            messages = [m for m in messages if m["timestamp"] < before_timestamp]
        
        messages.sort(key=lambda x: x["timestamp"], reverse=True)
        
        messages = messages[:limit]
        
        return messages
    
    def get_user_chatrooms(self, username):
        user_chatrooms = []
        
        for filename in os.listdir(self.chatrooms_dir):
            if filename.endswith('.json'):
                chatroom_file = os.path.join(self.chatrooms_dir, filename)
                with open(chatroom_file, 'r') as f:
                    chatroom_data = json.load(f)
                    
                    if username in chatroom_data["members"]:
                        user_chatrooms.append({
                            "id": chatroom_data["id"],
                            "name": chatroom_data["name"],
                            "creator": chatroom_data["creator"],
                            "members": chatroom_data["members"],
                            "created_at": chatroom_data["created_at"],
                            "message_count": len(chatroom_data["messages"])
                        })
        
        return user_chatrooms
    
    def create_direct_message(self, user1, user2):
        """Create or get direct message chatroom between two users
        
        Returns:
            (chatroom_id, is_new)
        """
        users = sorted([user1, user2])
        dm_name = f"DM_{users[0]}_{users[1]}"
        
        for filename in os.listdir(self.chatrooms_dir):
            if filename.endswith('.json'):
                chatroom_file = os.path.join(self.chatrooms_dir, filename)
                with open(chatroom_file, 'r') as f:
                    chatroom_data = json.load(f)
                    
                    if (chatroom_data["name"].startswith("DM_") and 
                        set(chatroom_data["members"]) == set(users) and
                        len(chatroom_data["members"]) == 2):
                        return chatroom_data["id"], False
        
        success, message, chatroom_id = self.create_chatroom(
            name=dm_name,
            creator=users[0],  # First user alphabetically is "creator"
            members=users
        )
        
        if success:
            return chatroom_id, True
        else:
            return None, False