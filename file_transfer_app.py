import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import struct
import json
from datetime import datetime
import zipfile
import tempfile
import shutil

class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network File Transfer")
        self.root.geometry("600x400")
        self.root.configure(bg="#2b2b2b")
        
        # Get local IP
        self.local_ip = self.get_local_ip()
        
        # Server thread
        self.server_thread = None
        self.server_running = False
        
        # Devices history
        self.devices_file = "devices_history.json"
        self.devices = self.load_devices()
        
        # Dropdown state
        self.dropdown_window = None
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background="#4a90e2", foreground="white")
        style.map("TButton", background=[('active', '#357abd')])
        style.configure("TLabel", background="#2b2b2b", foreground="white", font=("Arial", 10))
        style.configure("TEntry", fieldbackground="#3c3c3c", foreground="white")
        
        self.create_ui()
        self.start_server()
        
    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def load_devices(self):
        try:
            if os.path.exists(self.devices_file):
                with open(self.devices_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_devices(self):
        try:
            with open(self.devices_file, 'w') as f:
                json.dump(self.devices, f, indent=2)
        except Exception as e:
            print(f"Error saving devices: {e}")
    
    def add_device(self, ip, name=None):
        # Check if device already exists
        for device in self.devices:
            if device['ip'] == ip:
                # Update last used time
                device['last_used'] = datetime.now().isoformat()
                if name:
                    device['name'] = name
                self.save_devices()
                return
        
        # Add new device
        device = {
            'ip': ip,
            'name': name or ip,
            'last_used': datetime.now().isoformat()
        }
        self.devices.insert(0, device)
        
        # Keep only last 3 devices
        self.devices = self.devices[:3]
        self.save_devices()
    
    def show_device_dropdown(self, event=None):
        if not self.devices:
            return
        
        # Close existing dropdown
        if self.dropdown_window:
            self.dropdown_window.destroy()
        
        # Create dropdown window
        self.dropdown_window = tk.Toplevel(self.root)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.configure(bg="#3c3c3c", highlightthickness=1, highlightbackground="#4a90e2")
        
        # Position below the entry
        x = self.ip_entry.winfo_rootx()
        y = self.ip_entry.winfo_rooty() + self.ip_entry.winfo_height()
        self.dropdown_window.geometry(f"300x{len(self.devices) * 40}+{x}+{y}")
        
        # Add devices to dropdown
        for device in self.devices:
            frame = tk.Frame(self.dropdown_window, bg="#3c3c3c")
            frame.pack(fill=tk.X, padx=2, pady=1)
            
            btn = tk.Button(
                frame,
                text=f"{device['name']}\n{device['ip']}",
                bg="#3c3c3c",
                fg="white",
                font=("Arial", 9),
                relief=tk.FLAT,
                cursor="hand2",
                anchor=tk.W,
                padx=10,
                pady=5,
                command=lambda d=device: self.select_device(d)
            )
            btn.pack(fill=tk.BOTH, expand=True)
            
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#4a90e2"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#3c3c3c"))
        
        # Close dropdown when clicking outside
        self.dropdown_window.bind("<FocusOut>", lambda e: self.close_dropdown())
        self.root.bind("<Button-1>", lambda e: self.close_dropdown() if self.dropdown_window else None)
    
    def select_device(self, device):
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, device['ip'])
        self.close_dropdown()
    
    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
    
    def create_ui(self):
        # Title
        title_label = tk.Label(
            self.root, 
            text="📁 File Transfer", 
            font=("Arial", 20, "bold"),
            bg="#2b2b2b",
            fg="#4a90e2"
        )
        title_label.pack(pady=20)
        
        # Your IP Display
        ip_frame = tk.Frame(self.root, bg="#2b2b2b")
        ip_frame.pack(pady=10)
        
        ip_label = ttk.Label(ip_frame, text="Your IP Address:", font=("Arial", 11, "bold"))
        ip_label.pack(side=tk.LEFT, padx=5)
        
        ip_value = tk.Label(
            ip_frame,
            text=self.local_ip,
            font=("Arial", 12, "bold"),
            bg="#3c3c3c",
            fg="#4ade80",
            padx=15,
            pady=5,
            relief=tk.RAISED
        )
        ip_value.pack(side=tk.LEFT, padx=5)
        
        # Separator
        sep = tk.Frame(self.root, height=2, bg="#4a90e2")
        sep.pack(fill=tk.X, padx=50, pady=15)
        
        # Send File Section
        send_frame = tk.Frame(self.root, bg="#2b2b2b")
        send_frame.pack(pady=10, padx=40, fill=tk.X)
        
        ttk.Label(send_frame, text="Recipient IP:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ip_entry = tk.Entry(send_frame, width=25, bg="#3c3c3c", fg="white", insertbackground="white", font=("Arial", 10))
        self.ip_entry.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        self.ip_entry.bind("<FocusIn>", self.show_device_dropdown)
        self.ip_entry.bind("<Button-1>", self.show_device_dropdown)
        
        ttk.Label(send_frame, text="File/Folder:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_label = tk.Label(send_frame, text="No file or folder selected", bg="#3c3c3c", fg="#888888", 
                                   width=30, anchor=tk.W, padx=5, font=("Arial", 9))
        self.file_label.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg="#2b2b2b")
        button_frame.pack(pady=20)
        
        browse_file_btn = tk.Button(
            button_frame,
            text="📄 Browse File",
            command=self.browse_file,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        browse_file_btn.pack(side=tk.LEFT, padx=5)
        
        browse_folder_btn = tk.Button(
            button_frame,
            text="📁 Browse Folder",
            command=self.browse_folder,
            bg="#4a90e2",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        browse_folder_btn.pack(side=tk.LEFT, padx=5)
        
        send_btn = tk.Button(
            button_frame,
            text="📤 Send",
            command=self.send_file,
            bg="#4ade80",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=8,
            relief=tk.FLAT,
            cursor="hand2"
        )
        send_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="Listening for incoming files...",
            bg="#2b2b2b",
            fg="#888888",
            font=("Arial", 9, "italic")
        )
        self.status_label.pack(pady=10)
        
        self.selected_file = None
        self.selected_folder = None
        self.is_folder = False
    
    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select a file to send")
        if filename:
            self.selected_file = filename
            self.selected_folder = None
            self.is_folder = False
            self.file_label.config(text=os.path.basename(filename), fg="white")
    
    def browse_folder(self):
        foldername = filedialog.askdirectory(title="Select a folder to send")
        if foldername:
            self.selected_folder = foldername
            self.selected_file = None
            self.is_folder = True
            folder_name = os.path.basename(foldername)
            self.file_label.config(text=f"📁 {folder_name}", fg="white")
    
    def zip_folder(self, folder_path):
        """Create a temporary zip file of the folder"""
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zipf.write(file_path, arcname)
        
        return temp_zip.name
    
    def send_file(self):
        if not self.selected_file and not self.selected_folder:
            messagebox.showwarning("No Selection", "Please select a file or folder to send!")
            return
        
        recipient_ip = self.ip_entry.get().strip()
        if not recipient_ip:
            messagebox.showwarning("No IP", "Please enter recipient IP address!")
            return
        
        # Ask for device name if it's a new device
        device_exists = any(d['ip'] == recipient_ip for d in self.devices)
        if not device_exists:
            name_dialog = tk.Toplevel(self.root)
            name_dialog.title("Device Name")
            name_dialog.geometry("300x120")
            name_dialog.configure(bg="#2b2b2b")
            name_dialog.transient(self.root)
            name_dialog.grab_set()
            
            tk.Label(
                name_dialog,
                text="Enter a name for this device:",
                bg="#2b2b2b",
                fg="white",
                font=("Arial", 10)
            ).pack(pady=10)
            
            name_entry = tk.Entry(name_dialog, bg="#3c3c3c", fg="white", insertbackground="white", font=("Arial", 10))
            name_entry.pack(pady=5, padx=20, fill=tk.X)
            name_entry.insert(0, recipient_ip)
            name_entry.focus()
            
            device_name = [recipient_ip]  # Default to IP
            
            def save_name():
                device_name[0] = name_entry.get().strip() or recipient_ip
                name_dialog.destroy()
            
            tk.Button(
                name_dialog,
                text="OK",
                command=save_name,
                bg="#4a90e2",
                fg="white",
                font=("Arial", 10),
                relief=tk.FLAT,
                cursor="hand2"
            ).pack(pady=10)
            
            name_entry.bind("<Return>", lambda e: save_name())
            
            self.root.wait_window(name_dialog)
            
            # Add device to history
            self.add_device(recipient_ip, device_name[0])
        else:
            # Update last used time
            self.add_device(recipient_ip)
        
        thread = threading.Thread(target=self._send_file_thread, args=(recipient_ip,))
        thread.daemon = True
        thread.start()
    
    def _send_file_thread(self, recipient_ip):
        temp_zip_path = None
        try:
            self.status_label.config(text="Connecting...", fg="#fbbf24")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)  # Increased timeout for receiver to respond
            sock.connect((recipient_ip, 5555))
            
            # Prepare file info
            if self.is_folder:
                # Zip the folder
                self.status_label.config(text="Zipping folder...", fg="#fbbf24")
                temp_zip_path = self.zip_folder(self.selected_folder)
                file_to_send = temp_zip_path
                original_name = os.path.basename(self.selected_folder)
                filename = f"{original_name}.zip"
                is_folder = True
            else:
                file_to_send = self.selected_file
                filename = os.path.basename(self.selected_file)
                is_folder = False
            
            filesize = os.path.getsize(file_to_send)
            
            file_info = json.dumps({
                "filename": filename,
                "filesize": filesize,
                "is_folder": is_folder,
                "original_name": original_name if is_folder else None
            })
            sock.send(struct.pack("!I", len(file_info)))
            sock.send(file_info.encode())
            
            # Wait for receiver acceptance
            self.status_label.config(text="Waiting for receiver...", fg="#fbbf24")
            response = sock.recv(1024).decode()
            
            if response != "ACCEPT":
                sock.close()
                if temp_zip_path and os.path.exists(temp_zip_path):
                    os.unlink(temp_zip_path)
                self.status_label.config(text="Transfer declined by receiver", fg="#888888")
                return
            
            # Send file data
            display_name = f"folder '{original_name}'" if is_folder else f"file '{filename}'"
            self.status_label.config(text=f"Sending {display_name}...", fg="#fbbf24")
            with open(file_to_send, 'rb') as f:
                sent = 0
                while sent < filesize:
                    data = f.read(4096)
                    if not data:
                        break
                    sock.send(data)
                    sent += len(data)
            
            # Wait for completion confirmation
            self.status_label.config(text="Waiting for confirmation...", fg="#fbbf24")
            confirmation = sock.recv(1024).decode()
            
            sock.close()
            
            # Clean up temp zip
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            
            if confirmation == "SUCCESS":
                self.status_label.config(text="✓ Transfer successful!", fg="#4ade80")
                messagebox.showinfo("Success", f"{'Folder' if is_folder else 'File'} sent to {recipient_ip}")
            else:
                self.status_label.config(text="✗ Transfer failed on receiver", fg="#ef4444")
            
        except Exception as e:
            # Clean up temp zip on error
            if temp_zip_path and os.path.exists(temp_zip_path):
                os.unlink(temp_zip_path)
            
            self.status_label.config(text="✗ Transfer failed", fg="#ef4444")
            messagebox.showerror("Error", f"Failed to send: {str(e)}")
    
    def start_server(self):
        self.server_running = True
        self.server_thread = threading.Thread(target=self._server_thread)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def _server_thread(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', 5555))
        server.listen(5)
        
        while self.server_running:
            try:
                server.settimeout(1)
                client, addr = server.accept()
                thread = threading.Thread(target=self._handle_client, args=(client, addr))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except:
                break
    
    def _handle_client(self, client, addr):
        try:
            # Receive file info
            info_size = struct.unpack("!I", client.recv(4))[0]
            file_info = json.loads(client.recv(info_size).decode())
            
            filename = file_info["filename"]
            filesize = file_info["filesize"]
            is_folder = file_info.get("is_folder", False)
            original_name = file_info.get("original_name", None)
            
            # Show popup
            item_type = "folder" if is_folder else "file"
            display_name = original_name if is_folder else filename
            result = messagebox.askyesno(
                f"Incoming {item_type.title()}",
                f"Receive {item_type} from {addr[0]}?\n\n{item_type.title()}: {display_name}\nSize: {filesize / 1024:.2f} KB"
            )
            
            if not result:
                client.send("DECLINE".encode())
                client.close()
                return
            
            # Send acceptance
            client.send("ACCEPT".encode())
            
            if is_folder:
                # Ask where to extract the folder
                extract_dir = filedialog.askdirectory(title="Select where to extract folder")
                if not extract_dir:
                    client.send("FAIL".encode())
                    client.close()
                    return
                
                # Receive zip file to temp location
                temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                temp_zip.close()
                
                with open(temp_zip.name, 'wb') as f:
                    received = 0
                    while received < filesize:
                        data = client.recv(min(4096, filesize - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                
                # Extract the zip file
                try:
                    with zipfile.ZipFile(temp_zip.name, 'r') as zipf:
                        zipf.extractall(extract_dir)
                    
                    # Clean up temp zip
                    os.unlink(temp_zip.name)
                    
                    final_path = os.path.join(extract_dir, original_name)
                    client.send("SUCCESS".encode())
                    messagebox.showinfo("Success", f"Folder extracted to:\n{final_path}")
                except Exception as e:
                    if os.path.exists(temp_zip.name):
                        os.unlink(temp_zip.name)
                    client.send("FAIL".encode())
                    messagebox.showerror("Error", f"Failed to extract folder: {str(e)}")
            else:
                # Regular file handling
                save_path = filedialog.asksaveasfilename(
                    defaultextension="",
                    initialfile=filename,
                    title="Save file as"
                )
                
                if not save_path:
                    client.send("FAIL".encode())
                    client.close()
                    return
                
                with open(save_path, 'wb') as f:
                    received = 0
                    while received < filesize:
                        data = client.recv(min(4096, filesize - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)
                
                client.send("SUCCESS".encode())
                messagebox.showinfo("Success", f"File received and saved to:\n{save_path}")
            
            client.close()
            
        except Exception as e:
            try:
                client.send("FAIL".encode())
            except:
                pass
            messagebox.showerror("Error", f"Failed to receive: {str(e)}")
            client.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTransferApp(root)
    root.mainloop()