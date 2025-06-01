import customtkinter as ctk
from tkinter import filedialog
import os
import threading
from PIL import Image, ImageDraw
import json
import re

class Page2:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill=ctk.BOTH, expand=True)
        
        self.work_dir = "apk_work"
        rootPath = os.path.dirname(os.path.abspath(__file__))
        self.apktool_jar_path = os.path.join(rootPath, "apktool_2.11.1.jar")
        self.jdk_path = os.path.join(rootPath, r"jdk-21.0.7\bin\java.exe")
        
        self.icon_path = ""
        
        self.app_name = ""
        
        ctk.CTkLabel(self.frame, text="Page 2: Replace Icon and App name").pack(pady=10)
        
        icon_frame = ctk.CTkFrame(self.frame)
        icon_frame.pack(pady=5)

        self.label_icon = ctk.CTkLabel(icon_frame, text="Not selected icon file")
        self.label_icon.pack(pady=3)

        self.btn_choose_icon = ctk.CTkButton(icon_frame, text="Choose icon file", command=self.choose_icon)
        self.btn_choose_icon.pack(pady=3)

        self.btn_replace = ctk.CTkButton(icon_frame, text="Replace all icons", command=self.replace_icons, state=ctk.DISABLED)
        self.btn_replace.pack(pady=10)

        app_name_frame = ctk.CTkFrame(self.frame)
        app_name_frame.pack(pady=10)

        ctk.CTkLabel(app_name_frame, text="App Name:").pack(side=ctk.LEFT)
        self.app_name_entry = ctk.CTkEntry(app_name_frame)
        self.app_name_entry.pack(side=ctk.LEFT, padx=5)

        self.btn_change_name = ctk.CTkButton(app_name_frame, text="Change App Name", command=self.change_app_name, state=ctk.DISABLED)
        self.btn_change_name.pack(side=ctk.LEFT, padx=5)

        self.loading_label = ctk.CTkLabel(self.frame, text="")
        self.loading_label.pack()

        self.log_output = ctk.CTkTextbox(self.frame, width=600, height=200, corner_radius=0)
        self.log_output.pack(pady=5)

        self.refresh()

    def choose_icon(self):
        file_path = filedialog.askopenfilename(
            title="Choose icon file",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if file_path:
            self.icon_path = file_path
            self.label_icon.configure(text=f"Icon file: {file_path}")
            self.btn_replace.configure(state=ctk.NORMAL)
            self.log(f"Selected icon file: {file_path}")
            

    def replace_icons(self):
        self.log("\nSearching for icon sizes...")
        self.search_and_display_sizes()
        try:
            if not hasattr(self, 'icon_sizes') or not self.icon_sizes:
                self.error("No icon sizes found. Please extract APK first.")
                return
                
            if not hasattr(self, 'icon_path') or not self.icon_path:
                self.error("Not selected icon file")
                return
                
            try:
                with Image.open(self.icon_path) as img:
                    original_size = img.size
            except Exception as e:
                self.error(f"Cannot open icon file: {e}")
                return

            self.loading_label.configure(text="Replacing icons...")
            self.btn_replace.configure(state=ctk.DISABLED)
            self.btn_choose_icon.configure(state=ctk.DISABLED)
            
            threading.Thread(target=self.replace_icons_thread, daemon=True).start()
        except Exception as e:
            self.error(f"Error when replacing icons: {e}")
            self.reset_ui()

    def replace_icons_thread(self):
        try:
            with Image.open(self.icon_path) as img:
                for mipmap_dir, sizes in self.icon_sizes.items():
                    mipmap_path = os.path.join(self.work_dir, 'res', mipmap_dir)
                    if not os.path.isdir(mipmap_path):
                        self.log(f"Not found directory {mipmap_dir}")
                        continue
                        
                    self.log(f"\nProcessing directory {mipmap_dir}:")
                    
                    for icon, target_size in sizes.items():
                        target_path = os.path.join(mipmap_path, icon)
                        if not os.path.exists(target_path):
                            self.log(f"Not found file {icon}")
                            continue
                            
                        try:
                            resized_img = img.resize(target_size)
                            
                            if "round" in icon.lower() and "ic_launcher_background" not in icon:
                                mask = Image.new("L", target_size, 255)
                                draw = ImageDraw.Draw(mask)
                                
                                radius = min(target_size) * 0.2
                                
                                draw.rounded_rectangle((0, 0) + target_size, radius=radius, fill=255)
  
                                resized_img.putalpha(mask)
                            else:
                                resized_img = resized_img.convert("RGBA")
                            
                            resized_img.save(target_path, format='PNG')
                            self.log(f"Replaced {icon} with size {target_size[0]}x{target_size[1]}")
                            
                        except Exception as e:
                            self.log(f"Error when processing {icon}: {e}")
            
            self.log("\nCompleted replacing all icons!")
            
        except Exception as e:
            self.log(f"Error when replacing icons: {e}")
            
        finally:
            self.loading_label.configure(text="")
            self.btn_replace.configure(state=ctk.NORMAL)
            self.btn_choose_icon.configure(state=ctk.NORMAL)

    def search_and_display_sizes(self):
        try:
            res_dir = os.path.join(self.work_dir, 'res')
            if not os.path.exists(res_dir):
                self.log(f"Not found directory res")
                return

            icon_files = ['app_icon.png', 'app_icon_round.png', 'ic_launcher_background.png']
            
            mipmap_dirs = [d for d in os.listdir(res_dir) if d.startswith('mipmap')]
            
            if not mipmap_dirs:
                self.log("Not found mipmap directory")
                return
                
            for mipmap_dir in mipmap_dirs:
                mipmap_path = os.path.join(res_dir, mipmap_dir)
                if not os.path.isdir(mipmap_path):
                    continue
                
                for icon in icon_files:
                    file_path = os.path.join(mipmap_path, icon)
            icon_sizes = {}
            
            has_all_icons = False
            for mipmap_dir in mipmap_dirs:
                mipmap_path = os.path.join(res_dir, mipmap_dir)
                if not os.path.isdir(mipmap_path):
                    continue
                    
                found_icons = 0
                for icon in icon_files:
                    if os.path.exists(os.path.join(mipmap_path, icon)):
                        found_icons += 1
                if found_icons == len(icon_files):
                    has_all_icons = True
                    
                    sizes = {}
                    for icon in icon_files:
                        file_path = os.path.join(mipmap_path, icon)
                        try:
                            with Image.open(file_path) as img:
                                width, height = img.size
                                sizes[icon] = (width, height)
                        except Exception as e:
                            self.log(f"Not found size of {file_path}: {e}")
                    
                    icon_sizes[mipmap_dir] = sizes
            
            if not has_all_icons:
                self.log("Not found all icons")
            else:
                self.log("\nSize of icons:")
                self.log(json.dumps(icon_sizes, indent=2))
                
                self.icon_sizes = icon_sizes
                self.log("\nSaved information size icon to use for replacement later")
            
        except Exception as e:
            self.log(f"Error when searching file: {e}")

    def refresh(self):
        try:
            strings_path = os.path.join(self.work_dir, 'res', 'values', 'strings.xml')
            if os.path.exists(strings_path):
                with open(strings_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'<string name="app_name">(.*?)</string>', content)
                    if match:
                        self.app_name = match.group(1)
                        self.app_name_entry.delete(0, ctk.END)
                        self.app_name_entry.insert(0, self.app_name)
                        self.btn_change_name.configure(state=ctk.NORMAL)
                        self.log(f"Loaded app name: {self.app_name}")
                    else:
                        self.app_name_entry.delete(0, ctk.END)
                        self.log("Could not find app_name in strings.xml")
        except Exception as e:
            self.app_name_entry.delete(0, ctk.END)
            self.log(f"Error loading app name: {e}")

    def change_app_name(self):
        new_name = self.app_name_entry.get()
        if not new_name:
            self.error("Please enter a new app name")
            return

        try:
            strings_path = os.path.join(self.work_dir, 'res', 'values', 'strings.xml')
            if os.path.exists(strings_path):
                with open(strings_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = re.sub(r'(<string name="app_name">).*?(</string>)', 
                                    r'\g<1>' + new_name + r'\g<2>', 
                                    content)
                
                with open(strings_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                self.app_name = new_name
                self.log(f"Successfully changed app name to: {new_name}")
            else:
                self.error("strings.xml file not found")
        except Exception as e:
            self.error(f"Error changing app name: {e}")

    def log(self, msg):
        self.log_output.insert(ctk.END, f"{msg}\n")
        self.log_output.see(ctk.END)

    def error(self, msg):
        self.log(f"Error: {msg}")

    def reset_ui(self):
        self.loading_label.configure(text="")
        self.btn_replace.configure(state=ctk.NORMAL)
        self.btn_choose_icon.configure(state=ctk.NORMAL)
