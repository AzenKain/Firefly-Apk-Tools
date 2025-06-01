import customtkinter as ctk
from tkinter import filedialog
import os
import subprocess
import threading

CREATE_NO_WINDOW = 0x08000000

class Page1:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill=ctk.BOTH, expand=True)

        self.work_dir = "apk_work"
        rootPath = os.path.dirname(os.path.abspath(__file__))
        self.apktool_jar_path = os.path.join(rootPath, "apktool_2.11.1.jar")
        self.uber_jar_path = os.path.join(rootPath, "uber-apk-signer.jar")

        self.jdk_path = os.path.join(rootPath, r"jdk-21.0.7\bin\java.exe")
    
        self.apk_path = ""

        ctk.CTkLabel(self.frame, text="Page 1: Extract and compress APK").pack(pady=10)
        
        file_frame = ctk.CTkFrame(self.frame)
        file_frame.pack(pady=5)

        self.label_apk = ctk.CTkLabel(file_frame, text="Not selected APK file")
        self.label_apk.pack(pady=3)

        self.btn_choose_apk = ctk.CTkButton(file_frame, text="Choose APK file", command=self.choose_apk)
        self.btn_choose_apk.pack(pady=3)

        self.btn_extract = ctk.CTkButton(file_frame, text="Extract APK", command=self.extract_apk, state=ctk.DISABLED)
        self.btn_extract.pack(pady=10)

        name_frame = ctk.CTkFrame(self.frame)
        name_frame.pack(pady=10)

        ctk.CTkLabel(name_frame, text="APK output name:").pack(side=ctk.LEFT)
        self.name_entry = ctk.CTkEntry(name_frame, width=400)
        self.name_entry.insert(0, "StarRail")
        self.name_entry.pack(side=ctk.LEFT, padx=5)
        self.btn_compress = ctk.CTkButton(self.frame, text="Compress and sign APK", command=self.compress_apk)
        self.btn_compress.pack(pady=5)

        self.loading_label = ctk.CTkLabel(self.frame, text="")
        self.loading_label.pack(pady=5)
        
        self.log_output = ctk.CTkTextbox(self.frame, width=600, height=200, corner_radius=0)
        self.log_output.pack(pady=5)


    def compress_apk(self):
        if not self.work_dir:
            self.log_output.insert(ctk.END, "Not found work directory\n")
            return

        apk_name = self.name_entry.get()
        if not apk_name:
            self.log_output.insert(ctk.END, "Not found apk name\n")
            return

        self.loading_label.configure(text="Compressing APK...")
        self.btn_compress.configure(state=ctk.DISABLED)
        self.log_output.insert(ctk.END, f"Compressing APK {apk_name}...\n")
        
        threading.Thread(target=self.compress_apk_thread, daemon=True, args=(apk_name,)).start()

    def compress_apk_thread(self, apk_name):
        try:
            decompiled_dir = os.path.join(self.work_dir)
            compressed_apk = f"{apk_name}.apk"
            
            cmd = [self.jdk_path, 
                   "-jar", self.apktool_jar_path,
                   "b", decompiled_dir,
                   "-o", compressed_apk]
            
            self.log_output.insert(ctk.END, "Running apktool to compress...\n")
            
            process = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log(output.strip())
            rc = process.poll()

            if rc != 0:
                self.log(f"Error when compress APK: Process returned code {rc}")
                return False
                
            self.log("Signing APK using Uber...")
            

            if not os.path.exists(self.uber_jar_path):
                self.log(f"Error: Cannot find uber-apk-signer at {self.uber_jar_path}")
                self.log("Please make sure uber-apk-signer.jar is in the correct location")
                return False
            
            uber_cmd = [self.jdk_path,
                        "-jar", self.uber_jar_path,
                        "-a", compressed_apk]
            
            process = subprocess.Popen(uber_cmd, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log(output.strip())
            rc = process.poll()
            
            if rc != 0:
                self.log(f"Error when sign APK: Process returned code {rc}")
                return False
            
            signed_apk = f"{apk_name}-aligned-debugSigned.apk"
            signed_id = f"{apk_name}-aligned-debugSigned.apk.idsig"
            if os.path.exists(signed_apk):
                if os.path.exists(compressed_apk):
                    os.remove(compressed_apk)
                os.rename(signed_apk, compressed_apk)
                self.log(f"Successfully renamed signed APK to {compressed_apk}")
            else:
                self.log("Warning: Signed APK not found")

            if os.path.exists(signed_id):
                os.remove(signed_id)

            self.loading_label.configure(text="Completed!")
            self.log("Completed compressing and signing APK!")
            
        except Exception as e:
            self.log(f"Error: {str(e)}")
        finally:
            self.btn_compress.configure(state=ctk.NORMAL)


    def choose_apk(self):
        file_path = filedialog.askopenfilename(
            title="Choose APK file",
            filetypes=[("APK files", "*.apk")]
        )
        if file_path:
            self.apk_path = file_path
            self.label_apk.configure(text=f"File APK: {file_path}")
            self.btn_extract.configure(state=ctk.NORMAL)
            self.log(f"Selected APK file: {file_path}")

    def extract_apk(self):
        threading.Thread(target=self.extract_apk_thread, daemon=True).start()

    def extract_apk_thread(self):
        if not self.apk_path:
            self.log_output.insert(ctk.END, "Not found apk path\n")
            return

        try:
            self.loading_label.configure(text="Extracting APK...")
            self.btn_extract.configure(state=ctk.DISABLED)
            self.btn_choose_apk.configure(state=ctk.DISABLED)
            
            self.log_output.delete(1.0, ctk.END)
            
            if os.path.exists(self.work_dir):
                try:
                    import time
                    time.sleep(1)
                    
                    for root, dirs, files in os.walk(self.work_dir, topdown=False):
                        for name in files:
                            try:
                                file_path = os.path.join(root, name)
                                os.chmod(file_path, 0o777)
                                os.remove(file_path)
                            except Exception as e:
                                self.log(f"Cannot remove file {file_path}: {e}")
                        for name in dirs:
                            try:
                                dir_path = os.path.join(root, name)
                                os.rmdir(dir_path)
                            except Exception as e:
                                self.log(f"Cannot remove directory {dir_path}: {e}")
                    
                    try:
                        os.rmdir(self.work_dir)
                    except Exception as e:
                        self.log(f"Cannot remove directory {self.work_dir}: {e}")
                    
                    self.log(f"Deleted old folder {self.work_dir}")
                except Exception as e:
                    self.log(f"Error when removing folder {self.work_dir}: {e}")
                    return False

            decode_cmd = [self.jdk_path, "-jar", self.apktool_jar_path, "d", self.apk_path, "-f", "-o", self.work_dir]
            process = subprocess.Popen(decode_cmd, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log(output.strip())
            rc = process.poll()

            if rc == 0:
                self.log(f"Extracted APK to folder {self.work_dir}")
            else:
                self.log(f"Error when extracting APK: Process returned code {rc}")
                return False
        except Exception as e:
            self.log(f"Error when extracting APK: {e}")
            return False
        finally:
            self.loading_label.configure(text="")
            self.btn_extract.configure(state=ctk.NORMAL)
            self.btn_choose_apk.configure(state=ctk.NORMAL)

    def log(self, msg):
        self.log_output.insert(ctk.END, f"{msg}\n")
        self.log_output.see(ctk.END)
