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
from pathlib import Path

# Define allowed file types and size limit
ALLOWED_FILE_TYPES = [
    ('Text files', '*.txt'),
    ('PDF files', '*.pdf'),
    ('Images', '*.png *.jpg *.jpeg *.gif'),
    ('Documents', '*.doc *.docx'),
    ('All files', '*.*')  # Keep this for user convenience, validate after selection
]
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB limit

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("P2P Chat App")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.controller = NodeController()
    
        # Determine local IP address
        self.node_address = self.get_local_ip()
        if ":" not in self.node_address:
            self.node_address += ":7091"  # Add default port if needed
        
        self.connected_peers = {}
        self.selected_peer = None
        
        self.downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "P2PChatApp")
        os.makedirs(self.downloads_folder, exist_ok=True)
        
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.control_frame = ctk.CTkFrame(self.main_frame)
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.node_label = ctk.CTkLabel(self.control_frame, text="Node Address:")
        self.node_label.pack(side=tk.LEFT, padx=5)
        
        self.node_entry = ctk.CTkEntry(self.control_frame, width=150)
        self.node_entry.pack(side=tk.LEFT, padx=5)
        self.node_entry.insert(0, self.node_address)
        
        self.connect_button = ctk.CTkButton(self.control_frame, text="Connect", command=self.connect_to_node)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ctk.CTkButton(self.control_frame, text="Refresh Peers", command=self.refresh_peers)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.peers_frame = ctk.CTkFrame(self.content_frame)
        self.peers_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5, expand=False)
        
        self.peers_label = ctk.CTkLabel(self.peers_frame, text="Online Peers")
        self.peers_label.pack(padx=5, pady=5)
        
        self.peers_scrollable_frame = ctk.CTkScrollableFrame(self.peers_frame, width=150, height=400)
        self.peers_scrollable_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.add_peer_button = ctk.CTkButton(self.peers_frame, text="Add Peer", command=self.add_peer)
        self.add_peer_button.pack(padx=5, pady=5, fill=tk.X)

        self.chat_frame = ctk.CTkFrame(self.content_frame)
        self.chat_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5, expand=True)

        # Create the chat display with CustomTkinter's CTkTextbox
        self.chat_display = ctk.CTkTextbox(self.chat_frame, width=400, height=400)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_display.configure(state=tk.DISABLED)
        
        # Get the underlying tkinter Text widget from CTkTextbox for tag configuration
        self._text_widget = self.chat_display._textbox
        self._text_widget.tag_configure("status_tag", foreground="gray")
        
        # Create a dictionary to store tag callbacks for file downloads
        self.download_callbacks = {}

        self.message_frame = ctk.CTkFrame(self.chat_frame)
        self.message_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.message_entry = ctk.CTkEntry(self.message_frame, width=300)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ctk.CTkButton(self.message_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)
        
        self.file_button = ctk.CTkButton(self.message_frame, text="Send File", command=self.send_file)
        self.file_button.pack(side=tk.RIGHT, padx=5)
        
        self.update_peers_list()
        
        self.polling_active = True
        self.polling_thread = threading.Thread(target=self.poll_responses)
        self.polling_thread.daemon = True
        self.polling_thread.start()
    
    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return f"{ip}:7091"
        except Exception:
            return "127.0.0.1:7091"  # Fallback to localhost
        finally:
            s.close()

    def connect_to_node(self):
        self.node_address = self.node_entry.get()
        if not self.node_address:
            messagebox.showerror("Error", "Please enter a node address")
            return
        
        self.controller.submit_info(self.node_address)
        self.add_chat_message("System", f"Connected to node: {self.node_address}")
        
        self.message_entry.configure(state=tk.NORMAL)
        self.send_button.configure(state=tk.NORMAL)
        self.file_button.configure(state=tk.NORMAL)
        
        self.refresh_peers()
    
    def refresh_peers(self):
        if not self.node_address:
            messagebox.showerror("Error", "Please connect to a node first")
            return
        
        self.controller.submit_info(self.node_address)
        time.sleep(1)  
        
        response = self.controller.get_response(self.node_address)
        if response and "Tracker update" in response:
            self.add_chat_message("System", response)
            self.update_peers_list()
        else:
            self.add_chat_message("System", "Failed to refresh peers list")
    
    def update_peers_list(self):
        for widget in self.peers_scrollable_frame.winfo_children():
            widget.destroy()
    
        for peer in self.connected_peers:
            peer_button = ctk.CTkButton(
                self.peers_scrollable_frame, 
                text=peer,
                command=lambda p=peer: self.select_peer(p)
            )
            peer_button.pack(fill=tk.X, padx=2, pady=2)
    
    def add_peer(self):
        peer_address = simpledialog.askstring("Add Peer", "Enter peer address (e.g., 127.0.0.1:7092):")
        if not peer_address:
            return
        
        if not self.node_address:
            messagebox.showerror("Error", "Please connect to a node first")
            return
        
        self.controller.peer_connect(self.node_address, peer_address)
        self.add_chat_message("System", f"Connecting to peer: {peer_address}")
        
        self.connected_peers[peer_address] = {"messages": []}
        self.update_peers_list()
    
    def select_peer(self, peer):
        self.selected_peer = peer
        self.add_chat_message("System", f"Selected peer: {peer}")
        
        self.display_chat_history(peer)
    
    def display_chat_history(self, peer):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        
        # Clear all previous download callbacks
        self.download_callbacks.clear()
        
        if peer in self.connected_peers:
            for msg in self.connected_peers[peer].get("messages", []):
                sender = msg.get("sender", "Unknown")
                content = msg.get("content", "")
                
                if msg.get("type") == "file":
                    file_name = msg.get("filename", "unknown")
                    self.chat_display.insert(tk.END, f"{sender}: Sent file: {file_name}\n")
                    
                    # Add clickable download link if it's a received file
                    if sender != "You":
                        tag_name = f"file_{hash(file_name)}_{int(time.time()*1000)}"
                        
                        # Store file info in our callbacks dictionary
                        self.download_callbacks[tag_name] = msg
                        
                        # Insert clickable text with the tag
                        self.chat_display.insert(tk.END, "[Download File]\n")
                        
                        # Configure the tag for the underlying text widget
                        start_pos = self.chat_display._textbox.index(f"end-2l")
                        end_pos = self.chat_display._textbox.index(f"end-1l")
                        self.chat_display._textbox.tag_add(tag_name, start_pos, end_pos)
                        self.chat_display._textbox.tag_configure(tag_name, foreground="blue", underline=1)
                        self.chat_display._textbox.tag_bind(tag_name, "<Button-1>", 
                                              lambda e, t=tag_name: self.save_received_file(self.download_callbacks[t]))
                else:
                    self.chat_display.insert(tk.END, f"{sender}: {content}\n")
                    
                    # Show status for sent messages
                    if sender == "You" and "status" in msg:
                        status = msg.get("status", "")
                        self.chat_display.insert(tk.END, f"    {status}\n")
                        
                        # Apply status tag to the underlying text widget
                        start_pos = self.chat_display._textbox.index(f"end-2l")
                        end_pos = self.chat_display._textbox.index(f"end-1l")
                        self.chat_display._textbox.tag_add("status_tag", start_pos, end_pos)
        
        self.chat_display.configure(state=tk.DISABLED)
    
    def add_chat_message(self, sender, content):
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {content}\n")
        self.chat_display.see(tk.END)
        self.chat_display.configure(state=tk.DISABLED)
        
        if self.selected_peer and (sender == "You" or sender == self.selected_peer):
            if self.selected_peer not in self.connected_peers:
                self.connected_peers[self.selected_peer] = {"messages": []}
            
            self.connected_peers[self.selected_peer]["messages"].append({
                "sender": sender,
                "content": content,
                "timestamp": time.time()
            })
    
    def send_message(self, event=None):
        message = self.message_entry.get()
        if not message:
            return
        
        if not self.selected_peer:
            messagebox.showerror("Error", "Please select a peer first")
            return
        
        if not self.node_address:
            messagebox.showerror("Error", "Please connect to a node first")
            return
        
        self.controller.send_chat(self.node_address, self.selected_peer, message)
        
        self.add_chat_message("You", message)
        
        self.message_entry.delete(0, tk.END)
    
    def validate_file(self, file_path):
        # Check if file exists
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024:.1f} MB"
        
        # Check file extension - basic validation
        file_ext = os.path.splitext(file_path)[1].lower()
        valid_extensions = ['.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.doc', '.docx']
        
        if file_ext not in valid_extensions:
            return False, f"Invalid file type. Allowed types: {', '.join(valid_extensions)}"
            
        return True, "File valid"
    
    def send_file(self):
        if not self.selected_peer:
            messagebox.showerror("Error", "Please select a peer first")
            return
        
        if not self.node_address:
            messagebox.showerror("Error", "Please connect to a node first")
            return
        
        file_path = filedialog.askopenfilename(
            title="Select a file to send",
            filetypes=ALLOWED_FILE_TYPES
        )
        
        if not file_path:
            return  # User cancelled selection
        
        valid, message = self.validate_file(file_path)
        if not valid:
            messagebox.showerror("Invalid File", message)
            return
        
        # Read and encode the file
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_encoded = base64.b64encode(file_data).decode('utf-8')
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = os.path.splitext(file_path)[1]
            file_hash = hashlib.md5(file_data).hexdigest()
            
            # Create file message
            file_message = {
                "type": "file",
                "filename": file_name,
                "size": file_size,
                "filetype": file_type,
                "hash": file_hash,
                "data": file_encoded
            }
            
            # Send the file message
            self.controller.send_file(self.node_address, self.selected_peer, file_message)
            
            # Update UI and history
            if self.selected_peer not in self.connected_peers:
                self.connected_peers[self.selected_peer] = {"messages": []}
            
            self.connected_peers[self.selected_peer]["messages"].append({
                "sender": "You",
                "type": "file",
                "filename": file_name,
                "size": file_size,
                "filetype": file_type,
                "hash": file_hash,
                "timestamp": time.time()
            })
            
            self.add_chat_message("System", f"Sending file: {file_name} ({file_size/1024:.1f} KB)")
            self.display_chat_history(self.selected_peer)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send file: {str(e)}")
    
    def save_received_file(self, file_info):
        try:
            if "data" not in file_info:
                messagebox.showerror("Error", "File data not available")
                return
            
            file_name = file_info.get("filename", "received_file")
            file_data = base64.b64decode(file_info["data"])
            
            # Create a safe file path
            save_path = os.path.join(self.downloads_folder, file_name)
            count = 1
            while os.path.exists(save_path):
                base_name, ext = os.path.splitext(file_name)
                save_path = os.path.join(self.downloads_folder, f"{base_name}_{count}{ext}")
                count += 1
            
            # Save the file
            with open(save_path, 'wb') as file:
                file.write(file_data)
            
            messagebox.showinfo("File Downloaded", f"File saved to: {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def poll_responses(self):
        while self.polling_active:
            try:
                if self.node_address:
                    response = self.controller.get_response(self.node_address)
                    if response:
                        self.process_response(response)
            except Exception as e:
                print(f"Error polling responses: {e}")
            
            time.sleep(0.5)
    
    def process_response(self, response):
        if response.startswith("CHAT:"):
                parts = response.split(":", 2)
                if len(parts) >= 3:
                    peer = parts[1]
                    message = parts[2]
                    
                    if self.selected_peer == peer:
                        self.add_chat_message(peer, message)
                    else:
                        self.add_chat_message("System", f"New message from {peer}")
                        
                        if peer not in self.connected_peers:
                            self.connected_peers[peer] = {"messages": []}
                        
                        self.connected_peers[peer]["messages"].append({
                            "sender": peer,
                            "content": message,
                            "timestamp": time.time()
                        })
        elif response.startswith("DELIVERED:"):
            parts = response.split(":", 2)
            if len(parts) >= 3:
                peer = parts[1]
                message = parts[2]
                
                if self.selected_peer == peer:
                    # Update the last message with "delivered" status if it matches
                    self.update_message_status(peer, message, "✓ Delivered")
                
        elif response.startswith("FAILED:"):
            parts = response.split(":", 3)
            if len(parts) >= 4:
                peer = parts[1]
                message = parts[2]
                error = parts[3]
                
                if self.selected_peer == peer:
                    self.update_message_status(peer, message, f"❌ Failed: {error}")
                else:
                    self.add_chat_message("System", f"Failed to send message to {peer}: {error}")
        elif response.startswith("FILE:"):
            try:
                parts = response.split(":", 2)
                if len(parts) >= 3:
                    peer = parts[1]
                    file_data_str = parts[2]
                    file_data = json.loads(file_data_str)
                    
                    # Add to chat history
                    if peer not in self.connected_peers:
                        self.connected_peers[peer] = {"messages": []}
                    
                    self.connected_peers[peer]["messages"].append({
                        "sender": peer,
                        "type": "file",
                        "filename": file_data.get("filename", "unknown"),
                        "size": file_data.get("size", 0),
                        "filetype": file_data.get("filetype", ""),
                        "hash": file_data.get("hash", ""),
                        "data": file_data.get("data", ""),
                        "timestamp": time.time()
                    })
                    
                    # Update display if this peer is selected
                    if self.selected_peer == peer:
                        self.add_chat_message("System", f"Received file from {peer}: {file_data.get('filename')}")
                        self.display_chat_history(peer)
                    else:
                        self.add_chat_message("System", f"Received file from {peer}")
            except Exception as e:
                print(f"Error processing file: {e}")
        
        elif response.startswith("Peer ") and "connected" in response:
            try:
                peer = response.split(" ")[1]
                if peer not in self.connected_peers:
                    self.connected_peers[peer] = {"messages": []}
                    self.update_peers_list()
                    self.add_chat_message("System", f"New peer connected: {peer}")
            except Exception as e:
                print(f"Error processing peer connection: {e}")
        
        else:
            self.add_chat_message("System", response.strip())
            
    def update_message_status(self, peer, message_content, status):
        if peer not in self.connected_peers:
            return
        
        message_found = False
        for msg in self.connected_peers[peer]["messages"]:
            if msg.get("sender") == "You" and msg.get("content") == message_content:
                if "status" not in msg:
                    message_found = True
                    msg["status"] = status
                    break
        
        if message_found:
            self.display_chat_history(peer)

    def on_close(self):
        if self.node_address:
            self.controller.exit_node(self.node_address)
        
        self.polling_active = False
        
        self.root.destroy()

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatApp(root)
    root.mainloop()
