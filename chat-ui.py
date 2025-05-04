#!/usr/bin/env python3
import os
import json
import time
import socket
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import customtkinter as ctk
from node_controller import NodeController
import base64
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import io
import sys

from user_management import UserManager
from chatroom_manager import ChatroomManager
from lib.logging import create_frontend_logger

ALLOWED_FILE_TYPES = [
    ('Images', '*.png *.jpg *.jpeg *.gif'),
    ('Text files', '*.txt'),
    ('PDF files', '*.pdf'),
    ('Documents', '*.doc *.docx'),
    ('All files', '*.*')  
]
MAX_FILE_SIZE = 5 * 1024 * 1024 

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NetApp Chat")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.session_id = str(uuid.uuid4())[:8]
        self.logger = create_frontend_logger(self.session_id)
        self.logger.system("Application started", {"session_id": self.session_id})
        
        self.user_manager = UserManager()
        self.chatroom_manager = ChatroomManager()
        self.controller = NodeController()
        
        self.node_address = None
        self.current_user = None
        self.selected_chatroom = None
        self.selected_peer = None
        self.chatrooms = {} 
        self.peers = {}
        self.downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "NetApp")
        os.makedirs(self.downloads_folder, exist_ok=True)
    
        self.setup_login_ui()
        
        self.polling_active = False
    
    def get_local_ip(self):
        """Get local IP address"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return f"{ip}:7091"
        except Exception:
            return "127.0.0.1:7091"  # Fallback to localhost, CHANGE LATER
        finally:
            s.close()
    
    def setup_login_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.login_frame = ctk.CTkFrame(self.root)
        self.login_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        app_title = ctk.CTkLabel(self.login_frame, text="NetApp Chat", font=("Helvetica", 24, "bold"))
        app_title.pack(pady=(20, 40))
        
        login_form = ctk.CTkFrame(self.login_frame)
        login_form.pack(padx=20, pady=20)
        
        username_label = ctk.CTkLabel(login_form, text="Username:")
        username_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.username_entry = ctk.CTkEntry(login_form, width=200)
        self.username_entry.grid(row=0, column=1, padx=10, pady=10)
        
        password_label = ctk.CTkLabel(login_form, text="Password:")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.password_entry = ctk.CTkEntry(login_form, width=200, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        address_label = ctk.CTkLabel(login_form, text="Node Address:")
        address_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.address_entry = ctk.CTkEntry(login_form, width=200)
        self.address_entry.grid(row=2, column=1, padx=10, pady=10)
        self.address_entry.insert(0, self.get_local_ip())
        
        login_button = ctk.CTkButton(login_form, text="Login", command=self.login)
        login_button.grid(row=3, column=0, padx=10, pady=20)
        
        register_button = ctk.CTkButton(login_form, text="Register", command=self.register)
        register_button.grid(row=3, column=1, padx=10, pady=20)
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        node_address = self.address_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        success, message = self.user_manager.authenticate(username, password)
        if success:
            self.current_user = self.user_manager.get_current_user()
            self.node_address = node_address
            
            host, port = node_address.split(":")
            self.user_manager.update_user_address(username, host, port)
            
            self.controller.submit_info(node_address)           
            self.start_polling()
            self.setup_main_ui()
        else:
            messagebox.showerror("Login Failed", message)
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        node_address = self.address_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        host, port = node_address.split(":")
        
        success, message = self.user_manager.register_user(username, password, host, port)
        if success:
            messagebox.showinfo("Success", "Registration successful. You can now login.")
        else:
            messagebox.showerror("Registration Failed", message)
    
    def setup_main_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.sidebar = ctk.CTkFrame(self.main_frame, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        user_frame = ctk.CTkFrame(self.sidebar)
        user_frame.pack(fill=tk.X, padx=5, pady=5)
        
        user_label = ctk.CTkLabel(user_frame, text=f"Logged in as: {self.current_user['username']}")
        user_label.pack(pady=5)
        
        node_label = ctk.CTkLabel(user_frame, text=f"Node: {self.node_address}")
        node_label.pack(pady=5)
        
        button_frame = ctk.CTkFrame(self.sidebar)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        create_room_btn = ctk.CTkButton(button_frame, text="Create Chatroom", command=self.create_chatroom_dialog)
        create_room_btn.pack(fill=tk.X, pady=5)
        
        refresh_btn = ctk.CTkButton(button_frame, text="Refresh", command=self.refresh_all)
        refresh_btn.pack(fill=tk.X, pady=5)
        
        logout_btn = ctk.CTkButton(button_frame, text="Logout", command=self.logout)
        logout_btn.pack(fill=tk.X, pady=5)
        
        self.tab_view = ctk.CTkTabview(self.sidebar)
        self.tab_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.tab_view.add("Chatrooms")
        self.tab_view.add("Users")
        
        self.chatrooms_frame = ctk.CTkScrollableFrame(self.tab_view.tab("Chatrooms"))
        self.chatrooms_frame.pack(fill=tk.BOTH, expand=True)
        
        self.users_frame = ctk.CTkScrollableFrame(self.tab_view.tab("Users"))
        self.users_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.welcome_frame = ctk.CTkFrame(self.content_frame)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_label = ctk.CTkLabel(
            self.welcome_frame, 
            text="Welcome to NetApp Chat!",
            font=("Helvetica", 20, "bold")
        )
        welcome_label.pack(pady=(100, 10))
        
        instruction_label = ctk.CTkLabel(
            self.welcome_frame,
            text="Select a chatroom or user to start messaging",
            font=("Helvetica", 14)
        )
        instruction_label.pack()
        
        self.chat_frame = ctk.CTkFrame(self.content_frame)
        
        self.refresh_all()
    
    def refresh_all(self):
        for widget in self.chatrooms_frame.winfo_children():
            widget.destroy()
        
        for widget in self.users_frame.winfo_children():
            widget.destroy()
        
        user_chatrooms = self.chatroom_manager.get_user_chatrooms(self.current_user['username'])
        for chatroom in user_chatrooms:
            room_btn = ctk.CTkButton(
                self.chatrooms_frame,
                text=chatroom['name'],
                anchor="w",
                command=lambda room_id=chatroom['id']: self.select_chatroom(room_id)
            )
            room_btn.pack(fill=tk.X, pady=2)
            self.chatrooms[chatroom['id']] = chatroom
        
        all_users = self.user_manager.get_all_users()
        for user in all_users:
            if user['username'] != self.current_user['username']:
                user_btn = ctk.CTkButton(
                    self.users_frame,
                    text=user['username'],
                    anchor="w",
                    command=lambda username=user['username']: self.start_direct_message(username)
                )
                user_btn.pack(fill=tk.X, pady=2)
                self.peers[user['username']] = user
    
    def create_chatroom_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter chatroom name:", title="Create Chatroom")
        room_name = dialog.get_input()
        
        if room_name:
            success, message, chatroom_id = self.chatroom_manager.create_chatroom(
                name=room_name, 
                creator=self.current_user['username']
            )
            
            if success:
                messagebox.showinfo("Success", f"Chatroom '{room_name}' created")
                self.refresh_all()
            else:
                messagebox.showerror("Error", message)
    
    def select_chatroom(self, chatroom_id):
        self.selected_chatroom = chatroom_id
        self.selected_peer = None
        self.show_chat_area()
        
        chatroom = self.chatrooms.get(chatroom_id)
        if chatroom:
            self.chat_title_label.configure(text=f"Chatroom: {chatroom['name']}")
            
            self.member_var.set("Members")
            self.member_menu.configure(values=[
                f"{member}" for member in chatroom['members']
            ])
            
            self.load_chatroom_messages(chatroom_id)
    
    def start_direct_message(self, username):
        self.selected_peer = username
        self.selected_chatroom = None
        
        chatroom_id, is_new = self.chatroom_manager.create_direct_message(
            self.current_user['username'],
            username
        )
        
        if chatroom_id:
            self.selected_chatroom = chatroom_id
            self.show_chat_area()
            
            self.chat_title_label.configure(text=f"Chat with: {username}")
            
            self.member_var.set("Members")
            self.member_menu.configure(values=[
                self.current_user['username'],
                username
            ])
            
            self.load_chatroom_messages(chatroom_id)
        else:
            messagebox.showerror("Error", "Could not create direct message")
    
    def show_chat_area(self):
        self.welcome_frame.pack_forget()
        
        if hasattr(self, 'chat_frame') and self.chat_frame.winfo_children():
            self.chat_frame.pack(fill=tk.BOTH, expand=True)
            return
        
        self.chat_frame = ctk.CTkFrame(self.content_frame)
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ctk.CTkFrame(self.chat_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.chat_title_label = ctk.CTkLabel(header_frame, text="Chat", font=("Helvetica", 16, "bold"))
        self.chat_title_label.pack(side=tk.LEFT, padx=10)
        
        self.member_var = tk.StringVar()
        self.member_var.set("Members")
        
        self.member_menu = ctk.CTkOptionMenu(
            header_frame,
            variable=self.member_var,
            values=["No members"],
            command=self.on_member_selected
        )
        self.member_menu.pack(side=tk.RIGHT, padx=10)
        
        self.messages_frame = ctk.CTkScrollableFrame(self.chat_frame)
        self.messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        input_frame = ctk.CTkFrame(self.chat_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.attach_btn = ctk.CTkButton(
            input_frame, 
            text="📎", 
            width=40,
            command=self.attach_file
        )
        self.attach_btn.pack(side=tk.LEFT, padx=5)
        
        self.message_input = ctk.CTkTextbox(input_frame, height=40)
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.send_btn = ctk.CTkButton(
            input_frame, 
            text="Send", 
            width=80,
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT, padx=5)
        
        self.file_frame = ctk.CTkFrame(self.chat_frame)
        self.file_label = None
        self.attached_file = None
    
    def load_chatroom_messages(self, chatroom_id):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        messages = self.chatroom_manager.get_messages(chatroom_id, limit=50)
        
        messages.sort(key=lambda x: x['timestamp'])
        
        for msg in messages:
            self.display_message(msg)
    
    def display_message(self, message):
        is_own_message = message['sender'] == self.current_user['username']
        
        msg_frame = ctk.CTkFrame(
            self.messages_frame,
            fg_color=("lightblue" if is_own_message else "#f0f0f0")
        )
        
        if is_own_message:
            msg_frame.pack(anchor=tk.E, fill=tk.X, padx=10, pady=5)
        else:
            msg_frame.pack(anchor=tk.W, fill=tk.X, padx=10, pady=5)
        
        # Sender and timestamp
        header_frame = ctk.CTkFrame(msg_frame, fg_color="transparent")
        header_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        sender_label = ctk.CTkLabel(
            header_frame, 
            text=message['sender'], 
            font=("Helvetica", 12, "bold")
        )
        sender_label.pack(side=tk.LEFT)
        
        timestamp = datetime.fromtimestamp(message['timestamp']).strftime("%H:%M")
        time_label = ctk.CTkLabel(header_frame, text=timestamp, font=("Helvetica", 10))
        time_label.pack(side=tk.RIGHT)
        
        if message['type'] == 'text':
            content_label = ctk.CTkLabel(
                msg_frame, 
                text=message['content'],
                wraplength=400,
                justify=tk.LEFT
            )
            content_label.pack(fill=tk.X, padx=10, pady=5)
        
        elif message['type'] == 'file':
            file_info = message.get('file_info', {})
            filename = file_info.get('filename', 'File')
            
            file_frame = ctk.CTkFrame(msg_frame)
            file_frame.pack(fill=tk.X, padx=10, pady=5)
            
            file_icon = ctk.CTkLabel(file_frame, text="📄")
            file_icon.pack(side=tk.LEFT, padx=5)
            
            file_name = ctk.CTkLabel(file_frame, text=filename)
            file_name.pack(side=tk.LEFT, padx=5)
            
            download_btn = ctk.CTkButton(
                file_frame,
                text="Download",
                width=80,
                command=lambda m=message: self.download_file(m)
            )
            download_btn.pack(side=tk.RIGHT, padx=5)
    
    def send_message(self):
        if not self.selected_chatroom:
            messagebox.showerror("Error", "No chatroom selected")
            return
        
        message_text = self.message_input.get("1.0", tk.END).strip()
        
        if not message_text and not self.attached_file:
            messagebox.showerror("Error", "Message cannot be empty")
            return
        
        if self.attached_file:
            filename = os.path.basename(self.attached_file)
            file_size = os.path.getsize(self.attached_file)
            
            with open(self.attached_file, 'rb') as f:
                file_content = f.read()
            
            file_b64 = base64.b64encode(file_content).decode('utf-8')
            
            file_info = {
                'filename': filename,
                'size': file_size,
                'content': file_b64,
                'mime_type': self.get_mime_type(filename)
            }
            
            success, message, msg_data = self.chatroom_manager.add_message(
                self.selected_chatroom,
                self.current_user['username'],
                self.attached_file,
                message_type="file",
                file_info=file_info
            )
            
            self.clear_attachment()
            
        elif message_text:
            success, message, msg_data = self.chatroom_manager.add_message(
                self.selected_chatroom,
                self.current_user['username'],
                message_text
            )
            
            self.logger.chat_message(
                self.current_user['username'],
                self.selected_chatroom,
                message_text
            )
        
        self.message_input.delete("1.0", tk.END)
        
        if success:
            self.load_chatroom_messages(self.selected_chatroom)
        else:
            messagebox.showerror("Error", message)
    
    def attach_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a file to send",
            filetypes=ALLOWED_FILE_TYPES
        )
        
        if file_path:
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                messagebox.showerror(
                    "File Too Large", 
                    f"Maximum file size is {MAX_FILE_SIZE/1024/1024}MB"
                )
                return
            
            self.attached_file = file_path
            
            self.show_attachment(file_path)
    
    def show_attachment(self, file_path):
        self.clear_attachment()
        
        self.file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) / 1024  # KB
        
        file_info = ctk.CTkFrame(self.file_frame)
        file_info.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_label = ctk.CTkLabel(
            file_info, 
            text=f"📄 {file_name} ({file_size:.1f} KB)"
        )
        self.file_label.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ctk.CTkButton(
            file_info,
            text="✖",
            width=30,
            command=self.clear_attachment
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
    
    def clear_attachment(self):
        self.attached_file = None
        if hasattr(self, 'file_frame'):
            for widget in self.file_frame.winfo_children():
                widget.destroy()
            self.file_frame.pack_forget()
    
    def download_file(self, message):
        if message['type'] != 'file':
            return
        
        file_info = message.get('file_info', {})
        if not file_info:
            messagebox.showerror("Error", "File information not available")
            return
        
        filename = file_info.get('filename', 'downloaded_file')
        file_content_b64 = file_info.get('content')
        
        if not file_content_b64:
            messagebox.showerror("Error", "File content not available")
            return
        
        try:
            file_content = base64.b64decode(file_content_b64)
        except Exception as e:
            messagebox.showerror("Error", f"Could not decode file: {str(e)}")
            return
        
        save_path = os.path.join(self.downloads_folder, filename)
        
        counter = 1
        while os.path.exists(save_path):
            name, ext = os.path.splitext(filename)
            save_path = os.path.join(self.downloads_folder, f"{name}_{counter}{ext}")
            counter += 1
        
        try:
            with open(save_path, 'wb') as f:
                f.write(file_content)
            
            messagebox.showinfo(
                "Download Complete", 
                f"File saved to: {save_path}"
            )
            
            self.logger.file_transfer(
                message['sender'],
                self.current_user['username'],
                filename,
                len(file_content),
                "downloaded"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def get_mime_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        
        mime_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        
        return mime_types.get(ext, 'application/octet-stream')
    
    def on_member_selected(self, selected_member):
        if selected_member == "Members":
            return
        
        if self.selected_chatroom:
            messagebox.showinfo("User Info", f"Username: {selected_member}")
    
    def start_polling(self):
        if self.polling_active:
            return
        
        self.polling_active = True
        
        def poll_responses():
            while self.polling_active:
                if self.node_address:
                    response = self.controller.get_response(self.node_address)
                    if response:
                        self.process_node_response(response)
                
                time.sleep(0.5)
        
        self.polling_thread = threading.Thread(target=poll_responses, daemon=True)
        self.polling_thread.start()
    
    def process_node_response(self, response):
        try:
            command, data = response.split(':', 1)
            
            if command == "message":
                message_data = json.loads(data)
                
                if hasattr(self, 'selected_chatroom') and self.selected_chatroom == message_data.get('chatroom_id'):
                    self.load_chatroom_messages(self.selected_chatroom)
            
            elif command == "connection":
                connection_data = json.loads(data)
                status = connection_data.get('status')
                
                if status == "connected":
                    self.refresh_all()
        
        except Exception as e:
            self.logger.error(f"Error processing node response: {str(e)}")
    
    def logout(self):
        if self.current_user:
            if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
                self.polling_active = False
                if hasattr(self, 'polling_thread'):
                    self.polling_thread.join(1.0)
                
                if self.node_address:
                    self.controller.exit_node(self.node_address)
                
                self.logger.system("Application closed", {"session_id": self.session_id})
                
                self.root.destroy()
        else:
            self.root.destroy()

    def on_close(self):
        if self.node_address:
            self.controller.exit_node(self.node_address)
        
        self.polling_active = False
        
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatApp(root)
    app.run()