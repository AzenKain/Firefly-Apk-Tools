import customtkinter as ctk
import os
import threading
from re import sub
import re
from io import BufferedReader

class Page3:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill=ctk.BOTH, expand=True)
        
        self.work_dir = "apk_work"
        self.assets_dir = os.path.join(self.work_dir, "assets")
        self.server_env_config_path = os.path.join(self.assets_dir, "server_env_config.json")
        self.client_config_path = os.path.join(self.assets_dir, "ClientConfig.bytes")
    
        ctk.CTkLabel(self.frame, text="Page 3: Change Origin").pack(pady=10)
        
        origin_frame = ctk.CTkFrame(self.frame)
        origin_frame.pack(pady=5)

        ctk.CTkLabel(origin_frame, text="Origin:").pack(side=ctk.LEFT)
        self.origin_entry = ctk.CTkEntry(origin_frame, width=400)
        self.origin_entry.insert(0, "http://127.0.0.1:21000")
        self.origin_entry.pack(side=ctk.LEFT, padx=5)

        self.btn_change = ctk.CTkButton(self.frame, text="Change Origin", command=self.change_origin)
        self.btn_change.pack(pady=10)

        self.loading_label = ctk.CTkLabel(self.frame, text="")
        self.loading_label.pack()

        self.log_output = ctk.CTkTextbox(self.frame, width=600, height=200, corner_radius=0)
        self.log_output.pack(pady=5)

        self.refresh()

    def clear_log(self):
        self.log_output.configure(state="normal")
        self.log_output.delete("0.0", ctk.END)

    def refresh(self):
        if not os.path.exists(self.assets_dir) or not os.path.exists(self.server_env_config_path) or not os.path.exists(self.client_config_path):
            self.error("Not found assets directory")
        else:
            self.clear_log()

    def change_origin(self):
        threading.Thread(target=self.change_origin_thread, daemon=True).start()

    def change_origin_thread(self):
        try:
            assets_dir = os.path.join(self.work_dir, "assets")
            required_files = ["server_env_config.json", "ClientConfig.bytes"]
            missing_files = []
            
            for file in required_files:
                if not os.path.exists(os.path.join(assets_dir, file)):
                    missing_files.append(file)
            
            if len(missing_files) > 0:
                error_msg = f"Not found file in assets directory: {', '.join(missing_files)}"
                self.log(f"Error: {error_msg}")
                self.error(error_msg)
                return
            self.server_env_config_path = os.path.join(self.assets_dir, "server_env_config.json")
            self.client_config_path = os.path.join(self.assets_dir, "ClientConfig.bytes")

            origin = self.origin_entry.get()
            self.log(f"Changing origin to: {origin}")
            self.handler_change_origin(origin)
        except Exception as e:
            self.log(f"Error: {e}")
            self.error(str(e))
            
    def handler_change_origin(self, origin):
        with open(self.client_config_path, "rb") as f:
            data = bytearray()
            data += self.readOneByteString(f)
            data += self.readOneByteString(f)
            data += self.readOneByteString(f)
            data += self.readOneByteString(f)
            data += f.read(2)
            data += self.readArray(f, origin)
            data += f.read(16)

        with open(self.client_config_path, "wb") as f:
            f.write(data)
            self.log(f"Successfully changed origin in client_config to: {origin}")
        
        try:
            with open(self.server_env_config_path, "r", encoding='utf-8') as f:
                config_str = f.read()
            
            new_config_str = re.sub(r'https*://.+?([/"\?])', origin+"\\1", config_str)
            with open(self.server_env_config_path, "w", encoding='utf-8') as f:
                f.write(new_config_str)
            self.log(f"Successfully changed origin in server_env_config to: {origin}")
        except Exception as e:
            self.error(f"Error when processing server_env_config: {e}")
            return False

    def readOneByteString(self, f: BufferedReader):
        byte_length = f.read(2)
        length = int("0x" + byte_length.hex(), 0)
        string = f.read(length)
        return byte_length + string

    def readArray(self, f: BufferedReader, origin):
        out_bytes = []
        byte_length = f.read(2)
        length = int("0x" + byte_length.hex(), 0)
        out_bytes.append(byte_length)
        for i in range(length):
            byte_length = f.read(2)
            length = int("0x" + byte_length.hex(), 0)
            string = sub(r'https*://.+?([/"\?])', origin+"\\1", f.read(length).decode()).encode()
            out_bytes.append(bytes.fromhex(hex(len(string))[2:].zfill(4)))
            out_bytes.append(string)
        return b''.join(out_bytes)
        
    def log(self, msg):
        self.log_output.insert(ctk.END, f"{msg}\n")
        self.log_output.see(ctk.END)

    def error(self, msg):
        self.log(f"Error: {msg}")

    def reset_ui(self):
        self.loading_label.configure(text="")
        self.btn_change.configure(state=ctk.NORMAL)
