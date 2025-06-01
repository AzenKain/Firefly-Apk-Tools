import customtkinter as ctk
from tkinter import messagebox, ttk
import os
from page1 import Page1
from page2 import Page2
from page3 import Page3

class ApkIconChanger:
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        
        self.root = ctk.CTk()
        self.root.title("Firefly APK Tool")
        self.root.geometry("800x600")
        
        # Thêm logo
        try:
            rootPath = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(rootPath, "log.ico")
            if os.path.exists(logo_path):
                self.root.iconbitmap(logo_path)
        except Exception as e:
            print(f"Warning: Could not load logo: {e}")

        # Tạo notebook để chứa các trang
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=ctk.BOTH, expand=True)

        # Tạo các trang
        self.page1 = Page1(self.notebook)
        self.page2 = Page2(self.notebook)
        self.page3 = Page3(self.notebook)

        self.notebook.add(self.page1.frame, text="Extract and compress APK")
        self.notebook.add(self.page2.frame, text="Replace Icon and App name")
        self.notebook.add(self.page3.frame, text="Change Origin")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.root.mainloop()

    def on_tab_changed(self, event):
        selected_tab = event.widget.select()
        selected_frame = self.notebook.nametowidget(selected_tab)

        if selected_frame == self.page3.frame:
            self.page3.refresh()
        elif selected_frame == self.page2.frame:
            self.page2.refresh()

    def error(self, msg):
        messagebox.showerror("Lỗi", msg)

    def reset_ui(self):
        self.loading_label.config(text="")
        self.btn_extract.config(state=ctk.NORMAL)
        self.btn_choose_apk.config(state=ctk.NORMAL)
        self.btn_replace.config(state=ctk.DISABLED)
        self.label_icon.config(text="Chưa chọn file ảnh")
        self.icon_path = ""
        self.btn_choose_icon.config(state=ctk.NORMAL)

if __name__ == "__main__":
    app = ApkIconChanger()
