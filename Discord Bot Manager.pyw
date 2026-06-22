import customtkinter as ctk
import subprocess, os, sys, threading, time, psutil, pystray, json, shutil, webbrowser
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk
from tkinter import filedialog, messagebox

CUSTOM_PYTHON = r"C:\Users\M A\AppData\Local\Programs\Python\Python311\python.exe"
PYTHON_EXE = CUSTOM_PYTHON if os.path.exists(CUSTOM_PYTHON) else (shutil.which("python") or "python")

CREATE_NO_WINDOW = 0x08000000
CONFIG_FILE = "config.json"

if not os.path.exists("Logs"):
    os.makedirs("Logs")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ICON_PNG = resource_path("icon.png")
ICON_ICO = resource_path("icon.ico")

BG_COLOR = "#0A0A0F"          
FRAME_COLOR = "#12121A"       
ACCENT_COLOR = "#5865F2"      
TEXT_MAIN = "#FFFFFF"
TEXT_SUB = "#8A8A9E"
SUCCESS = "#57F287"           
ERROR = "#ED4245"             
WARNING = "#FEE75C" 
INFO_COLOR = "#00F0FF"

LANG = {
    "AR": {
        "TITLE": "GALAXY DISCORD BOT MANAGER",
        "SUB": "The Ultimate Production-Grade Dashboard for Discord Bots",
        "INSTALL": "⚡ تثبيت مكتبة ديسكورد الافتراضية",
        "STOP_ALL": "🛑 إيقاف الكل",
        "RESTART_ALL": "🔄 إعادة تشغيل الكل",
        "ADD_BOT": "➕ إضافة بوت جديد",
        "START_ALL": "🟢 تشغيل الكل",
        "DEV": "© Developer: M A",
        "CONTACT": "🌐 تواصل معي",
        "DELETE": "حذف",
        "RENAME": "تسمية",
        "PATH": "المسار",
        "LOGS": "السجل",
        "RESTART": "إعادة",
        "STOP": "إيقاف",
        "START": "تشغيل",
        "STATUS_OFF": "متوقف",
        "STATUS_ON": "يعمل",
        "STATUS_MISSING": "مفقود",
        "STATUS_RESTART": "إعادة تشغيل",
        "LOG_TITLE": "سجل النظام",
        "AUTO_SCROLL": "التمرير التلقائي",
        "CLEAR": "مسح",
        "BACK": "رجوع",
        "RESTART_BOT": "🔄 إعادة تشغيل البوت"
    },
    "EN": {
        "TITLE": "GALAXY DISCORD BOT MANAGER",
        "SUB": "The Ultimate Production-Grade Dashboard for Discord Bots",
        "INSTALL": "⚡ Install Discord.py Library",
        "STOP_ALL": "🛑 Stop All",
        "RESTART_ALL": "🔄 Restart All",
        "ADD_BOT": "➕ Add New Bot",
        "START_ALL": "🟢 Start All",
        "DEV": "© Developer: M A",
        "CONTACT": "🌐 Contact Me",
        "DELETE": "Delete",
        "RENAME": "Rename",
        "PATH": "Path",
        "LOGS": "Logs",
        "RESTART": "Restart",
        "STOP": "Stop",
        "START": "Start",
        "STATUS_OFF": "Offline",
        "STATUS_ON": "Online",
        "STATUS_MISSING": "Missing",
        "STATUS_RESTART": "Restarting",
        "LOG_TITLE": "System Logs",
        "AUTO_SCROLL": "Auto Scroll",
        "CLEAR": "Clear",
        "BACK": "Back",
        "RESTART_BOT": "🔄 Restart Bot"
    }
}

ctk.set_appearance_mode("dark")

class GalaxyDiscordManager(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = self.load_config()
        self.lang = self.config_data.get("lang", "AR")
        self.bots = self.config_data.get("bots", {})

        self.title(LANG[self.lang]["TITLE"])
        self.geometry("1200x750")
        self.configure(fg_color=BG_COLOR)

        try:
            if os.path.exists(ICON_PNG):
                self.app_icon = ImageTk.PhotoImage(Image.open(ICON_PNG))
                self.wm_iconphoto(True, self.app_icon)
            elif os.path.exists(ICON_ICO):
                self.iconbitmap(ICON_ICO)
        except: pass

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.processes = {}
        self.status_labels = {}
        self.ram_labels = {}
        self.uptime_labels = {}
        self.start_times = {}
        self.bot_rows = {}

        self.bot_logs = {name: [] for name in self.bots.keys()}
        self.manual_stop_flags = {name: False for name in self.bots.keys()}
        self.current_log_bot = None

        self.setup_ui()
        self.setup_log_page()
        self.log_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

        self.load_saved_bots()
        self.update_ui_loop()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
            except: return {}
        return {"lang": "AR", "bots": {}}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"lang": self.lang, "bots": self.bots}, f, indent=4, ensure_ascii=False)
        except: pass

    def switch_lang(self):
        self.lang = "EN" if self.lang == "AR" else "AR"
        self.save_config()
        self.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def load_saved_bots(self):
        for row in self.bot_rows.values(): row.destroy()
        self.bot_rows.clear()
        
        for name, path in self.bots.items():
            self.create_bot_row(name, path)
            if name in self.processes and self.processes[name].poll() is None:
                self.status_labels[name].configure(text=LANG[self.lang]["STATUS_ON"], text_color=SUCCESS)
            else:
                self.status_labels[name].configure(text=LANG[self.lang]["STATUS_OFF"], text_color=ERROR)

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        header_frame = ctk.CTkFrame(self.main_frame, fg_color=BG_COLOR)
        header_frame.pack(pady=(20, 10), fill="x")

        lang_btn = ctk.CTkButton(header_frame, text="English" if self.lang == "AR" else "عربي", width=80, fg_color="#1A1A24", hover_color="#262633", command=self.switch_lang)
        lang_btn.pack(side="top", anchor="e", padx=30)

        ctk.CTkLabel(header_frame, text=LANG[self.lang]["TITLE"], font=("Segoe UI Black", 28, "bold"), text_color=ACCENT_COLOR).pack()
        ctk.CTkLabel(header_frame, text=LANG[self.lang]["SUB"], font=("Arial", 13), text_color=TEXT_SUB).pack(pady=5)

        self.btn_install = ctk.CTkButton(header_frame, text=LANG[self.lang]["INSTALL"], font=("Arial", 12, "bold"), fg_color="#1F234A", hover_color="#2D336D", text_color=INFO_COLOR, height=32, command=self.start_library_installation)
        self.btn_install.pack(pady=5)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=FRAME_COLOR, width=1100, height=350, corner_radius=8)
        self.scroll_frame.pack(pady=10, padx=20, expand=True, fill="both")

        control_frame = ctk.CTkFrame(self.main_frame, fg_color=BG_COLOR)
        control_frame.pack(pady=15)

        ctk.CTkButton(control_frame, text=LANG[self.lang]["STOP_ALL"], font=("Arial", 14, "bold"), fg_color="#33141A", hover_color="#4D1A24", text_color=ERROR, width=150, height=40, command=self.stop_all).pack(side="left", padx=8)
        ctk.CTkButton(control_frame, text=LANG[self.lang]["RESTART_ALL"], font=("Arial", 14, "bold"), fg_color="#332A15", hover_color="#4D3F1F", text_color=WARNING, width=160, height=40, command=self.restart_all).pack(side="left", padx=8)
        ctk.CTkButton(control_frame, text=LANG[self.lang]["ADD_BOT"], font=("Arial", 14, "bold"), fg_color="#1A1A2E", hover_color="#2A2A4A", text_color=ACCENT_COLOR, width=180, height=40, command=self.add_bot_dialog).pack(side="left", padx=8)
        ctk.CTkButton(control_frame, text=LANG[self.lang]["START_ALL"], font=("Arial", 14, "bold"), fg_color="#0A2918", hover_color="#0F3D24", text_color=SUCCESS, width=150, height=40, command=self.start_all).pack(side="left", padx=8)

        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=35)
        footer_frame.pack(side="bottom", fill="x", pady=(0, 10), padx=30)

        ctk.CTkButton(footer_frame, text=LANG[self.lang]["DEV"], font=("Arial", 12, "bold"), fg_color="transparent", text_color=TEXT_SUB, hover_color=FRAME_COLOR, command=lambda: messagebox.showinfo("Info", "Developed by: M A")).pack(side="left")
        ctk.CTkButton(footer_frame, text=LANG[self.lang]["CONTACT"], font=("Arial", 12, "bold"), fg_color="#1A1A24", hover_color="#262633", text_color=INFO_COLOR, command=lambda: webbrowser.open("https://linktr.ee/m_150a")).pack(side="right")

    def create_bot_row(self, name, path):
        row = ctk.CTkFrame(self.scroll_frame, fg_color=BG_COLOR, corner_radius=6)
        row.pack(fill="x", pady=5, padx=10)
        self.bot_rows[name] = row

        ctk.CTkLabel(row, text=name, font=("Arial", 15, "bold"), text_color=TEXT_MAIN, width=140, anchor="w").pack(side="left", padx=15, pady=12)
        
        self.status_labels[name] = ctk.CTkLabel(row, text=LANG[self.lang]["STATUS_OFF"], font=("Arial", 13, "bold"), text_color=ERROR, width=80, anchor="w")
        self.status_labels[name].pack(side="left", padx=5)

        self.uptime_labels[name] = ctk.CTkLabel(row, text="⏱ 00:00:00", font=("Consolas", 13), text_color=TEXT_SUB, width=100)
        self.uptime_labels[name].pack(side="left", padx=5)

        self.ram_labels[name] = ctk.CTkLabel(row, text="0.0 MB", font=("Consolas", 13), text_color=TEXT_SUB, width=80, anchor="e")
        self.ram_labels[name].pack(side="left", padx=10)

        ctk.CTkButton(row, text=LANG[self.lang]["DELETE"], width=55, font=("Arial", 12), fg_color="#33141A", hover_color="#4D1A24", text_color=ERROR, command=lambda n=name: self.delete_bot(n)).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["RENAME"], width=55, font=("Arial", 12), fg_color="transparent", text_color=TEXT_SUB, hover_color="#12121A", command=lambda n=name: self.rename_bot_dialog(n)).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["PATH"], width=55, font=("Arial", 12), fg_color="transparent", text_color=TEXT_SUB, hover_color="#12121A", command=lambda p=path: os.startfile(os.path.dirname(p)) if os.path.exists(os.path.dirname(p)) else messagebox.showwarning("Error", "Folder not found!")).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["LOGS"], width=65, font=("Arial", 12), fg_color="transparent", border_color="#262633", border_width=1, text_color=TEXT_SUB, hover_color="#12121A", command=lambda n=name: self.show_logs(n)).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["RESTART"], width=55, font=("Arial", 12, "bold"), fg_color="transparent", border_color="#332A15", border_width=1, text_color=WARNING, hover_color="#1A140A", command=lambda n=name, p=path: self.restart_bot(n, p)).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["STOP"], width=65, font=("Arial", 12, "bold"), fg_color="transparent", border_color="#33141A", border_width=1, text_color=ERROR, hover_color="#1A0A0D", command=lambda n=name: self.stop_bot(n)).pack(side="right", padx=3)
        ctk.CTkButton(row, text=LANG[self.lang]["START"], width=65, font=("Arial", 12, "bold"), fg_color="#1A1A2E", hover_color="#2A2A4A", text_color=ACCENT_COLOR, command=lambda n=name, p=path: self.start_bot(n, p)).pack(side="right", padx=5)

    def start_library_installation(self):
        self.btn_install.configure(state="disabled", text="⏳...")
        threading.Thread(target=self.install_libraries_worker, daemon=True).start()

    def install_libraries_worker(self):
        try:
            process = subprocess.run([PYTHON_EXE, "-m", "pip", "install", "--upgrade", "discord.py"], creationflags=CREATE_NO_WINDOW, capture_output=True, text=True)
            if process.returncode == 0:
                messagebox.showinfo("Success", "discord.py installed/upgraded successfully!")
            else:
                messagebox.showerror("Error", str(process.stderr))
        except Exception: pass
        finally:
            self.btn_install.configure(state="normal", text=LANG[self.lang]["INSTALL"])

    def rename_bot_dialog(self, old_name):
        if old_name in self.processes and self.processes[old_name].poll() is None:
            messagebox.showwarning("Warning", "Stop the bot first!")
            return
        dialog = ctk.CTkInputDialog(text="New Name:", title=LANG[self.lang]["RENAME"])
        new_name = dialog.get_input()
        if not new_name: return
        new_name = new_name.strip()
        if new_name == old_name or new_name in self.bots: return
        
        self.bots[new_name] = self.bots.pop(old_name)
        self.save_config()
        self.bot_logs[new_name] = self.bot_logs.pop(old_name, [])
        self.manual_stop_flags[new_name] = self.manual_stop_flags.pop(old_name, False)
        
        for temp_dict in (self.status_labels, self.ram_labels, self.uptime_labels, self.start_times):
            if old_name in temp_dict: temp_dict[new_name] = temp_dict.pop(old_name)
        self.load_saved_bots()

    def restart_bot(self, name, path):
        def run_restart():
            self.stop_bot(name)
            self.append_log(name, "⏳ Restarting...\n", "warning")
            time.sleep(1.5)
            self.start_bot(name, path)
        threading.Thread(target=run_restart, daemon=True).start()

    def restart_all(self):
        for name, path in list(self.bots.items()): self.restart_bot(name, path)

    def add_bot_dialog(self):
        dialog = ctk.CTkInputDialog(text="Bot Name:", title=LANG[self.lang]["ADD_BOT"])
        bot_name = dialog.get_input()
        if not bot_name: return
        bot_name = bot_name.strip()
        if bot_name in self.bots: return
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if not file_path: return

        self.bots[bot_name] = file_path
        self.save_config()
        self.bot_logs[bot_name] = []
        self.manual_stop_flags[bot_name] = False
        self.create_bot_row(bot_name, file_path)

    def delete_bot(self, name):
        if messagebox.askyesno("Delete", f"Delete {name}?"):
            self.stop_bot(name)
            if name in self.bots:
                del self.bots[name]
                self.save_config()
            if name in self.bot_rows:
                self.bot_rows[name].destroy()
                del self.bot_rows[name]
            for temp_dict in (self.bot_logs, self.manual_stop_flags, self.status_labels, self.ram_labels, self.uptime_labels, self.start_times):
                temp_dict.pop(name, None)

    def setup_log_page(self):
        self.log_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        top_bar = ctk.CTkFrame(self.log_frame, fg_color=BG_COLOR)
        top_bar.pack(fill="x", pady=(30, 15), padx=30)

        ctk.CTkButton(top_bar, text=LANG[self.lang]["BACK"], width=90, fg_color="#1A1A24", hover_color="#262633", command=self.show_main).pack(side="left")
        self.log_title = ctk.CTkLabel(top_bar, text=LANG[self.lang]["LOG_TITLE"], font=("Arial", 18, "bold"), text_color=TEXT_MAIN)
        self.log_title.pack(side="left", padx=20)
        
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(top_bar, text=LANG[self.lang]["AUTO_SCROLL"], variable=self.auto_scroll_var, progress_color=ACCENT_COLOR).pack(side="left", padx=20)

        ctk.CTkButton(top_bar, text=LANG[self.lang]["CLEAR"], width=80, fg_color="transparent", border_color="#33141A", border_width=1, text_color=ERROR, command=self.clear_logs).pack(side="right", padx=5)
        ctk.CTkButton(top_bar, text=LANG[self.lang]["RESTART_BOT"], width=150, fg_color="transparent", border_color="#332A15", border_width=1, text_color=WARNING, command=self.restart_current_bot).pack(side="right", padx=5)
        ctk.CTkButton(top_bar, text=LANG[self.lang]["STOP"], width=80, fg_color="transparent", border_color="#33141A", border_width=1, text_color=ERROR, command=self.stop_current_bot).pack(side="right", padx=5)
        ctk.CTkButton(top_bar, text=LANG[self.lang]["START"], width=80, fg_color="#1A1A2E", text_color=ACCENT_COLOR, command=self.start_current_bot).pack(side="right", padx=5)

        self.log_box = ctk.CTkTextbox(self.log_frame, fg_color="#050508", text_color="#E0E0E0", font=("Consolas", 13), wrap="word", corner_radius=6, border_color="#1A1A24", border_width=1)
        self.log_box.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        self.log_box.tag_config("error", foreground=ERROR)
        self.log_box.tag_config("warning", foreground=WARNING)
        self.log_box.tag_config("info", foreground=INFO_COLOR)
        self.log_box.tag_config("system", foreground=ACCENT_COLOR)
        self.log_box.tag_config("success", foreground=SUCCESS)

    def restart_current_bot(self):
        if self.current_log_bot and self.current_log_bot in self.bots:
            self.restart_bot(self.current_log_bot, self.bots[self.current_log_bot])

    def start_current_bot(self):
        if self.current_log_bot and self.current_log_bot in self.bots: self.start_bot(self.current_log_bot, self.bots[self.current_log_bot])

    def stop_current_bot(self):
        if self.current_log_bot: self.stop_bot(self.current_log_bot)

    def show_logs(self, name):
        self.current_log_bot = name
        self.log_title.configure(text=f"{LANG[self.lang]['LOG_TITLE']}: {name}")
        self.refresh_textbox()
        self.main_frame.pack_forget()
        self.log_frame.pack(fill="both", expand=True)

    def show_main(self):
        self.current_log_bot = None
        self.log_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def clear_logs(self):
        if self.current_log_bot:
            self.bot_logs[self.current_log_bot].clear()
            self.refresh_textbox()

    def refresh_textbox(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        if self.current_log_bot and self.current_log_bot in self.bot_logs:
            for msg, tag in self.bot_logs[self.current_log_bot]:
                if tag: self.log_box.insert("end", msg, tag)
                else: self.log_box.insert("end", msg)
        if self.auto_scroll_var.get(): self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def write_to_file(self, name, message):
        try:
            with open(f"Logs/{name}_log.txt", "a", encoding="utf-8") as f: f.write(message)
        except: pass

    def append_log(self, name, message, tag=None):
        if name in self.bot_logs:
            self.bot_logs[name].append((message, tag))
            self.write_to_file(name, message)

    def read_process_output(self, process, name, path):
        for line in iter(process.stdout.readline, ''):
            if not line: break
            time_now = datetime.now().strftime("%H:%M:%S")
            upper_line = line.upper()
            tag = None
            if "ERROR" in upper_line or "TRACEBACK" in upper_line or "CRITICAL" in upper_line or "EXCEPTION" in upper_line: tag = "error"
            elif "WARNING" in upper_line: tag = "warning"
            elif "INFO" in upper_line: tag = "info"
            self.append_log(name, f"[{time_now}] {line}", tag)
            
        process.stdout.close()
        process.wait()
        self.start_times.pop(name, None)

        if name in self.manual_stop_flags and self.manual_stop_flags[name]:
            if name in self.status_labels: self.status_labels[name].configure(text=LANG[self.lang]["STATUS_OFF"], text_color=ERROR)
            self.append_log(name, f"\n--- Stopped manually ---\n", "system")
        else:
            if name in self.status_labels: self.status_labels[name].configure(text=LANG[self.lang]["STATUS_RESTART"], text_color=WARNING)
            self.append_log(name, f"\n--- Crash detected. Restarting... ---\n", "warning")
            time.sleep(5)
            if name in self.manual_stop_flags and not self.manual_stop_flags[name] and name in self.bots: 
                self.start_bot(name, self.bots[name])

    def start_bot(self, name, path):
        if name in self.processes and self.processes[name].poll() is None: return
        if not os.path.exists(path):
            self.manual_stop_flags[name] = True
            self.status_labels[name].configure(text=LANG[self.lang]["STATUS_MISSING"], text_color=ERROR)
            self.append_log(name, f"❌ File missing: {path}\n", "error")
            return
        try:
            self.manual_stop_flags[name] = False
            p = subprocess.Popen(
                [PYTHON_EXE, "-X", "utf8", "-u", path], 
                cwd=os.path.dirname(path),
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW
            )
            self.processes[name] = p
            self.start_times[name] = datetime.now()
            self.status_labels[name].configure(text=LANG[self.lang]["STATUS_ON"], text_color=SUCCESS)
            self.append_log(name, f"--- Started Successfully ---\n", "success")
            threading.Thread(target=self.read_process_output, args=(p, name, path), daemon=True).start()
        except Exception as e:
            self.append_log(name, f"Error: {e}\n", "error")

    def stop_bot(self, name):
        if name in self.processes and self.processes[name].poll() is None:
            self.manual_stop_flags[name] = True
            self.processes[name].terminate()

    def start_all(self):
        for name, path in self.bots.items(): self.start_bot(name, path)

    def stop_all(self):
        for name in list(self.bots.keys()): self.stop_bot(name)

    def hide_to_tray(self):
        self.withdraw()
        if os.path.exists(ICON_ICO): image = Image.open(ICON_ICO)
        elif os.path.exists(ICON_PNG): image = Image.open(ICON_PNG)
        else:
            image = Image.new('RGB', (64, 64), color=BG_COLOR)
            d = ImageDraw.Draw(image)
            d.ellipse((16, 16, 48, 48), fill=ACCENT_COLOR)

        menu = pystray.Menu(pystray.MenuItem('Show', self.show_from_tray), pystray.MenuItem('Exit', self.quit_app))
        self.tray_icon = pystray.Icon("GALAXY", image, "GALAXY Control Panel", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def show_from_tray(self, icon, item):
        icon.stop()
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        if icon: icon.stop()
        self.stop_all()
        self.destroy()
        os._exit(0)

    def update_ui_loop(self):
        if self.current_log_bot:
            current_lines = len(self.log_box.get("0.0", "end").splitlines())
            actual_lines = len(self.bot_logs.get(self.current_log_bot, []))
            if current_lines - 1 != actual_lines: self.refresh_textbox()

        for name, p in list(self.processes.items()):
            if p.poll() is None:
                if name in self.start_times:
                    delta = datetime.now() - self.start_times[name]
                    hours, remainder = divmod(delta.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if name in self.uptime_labels: self.uptime_labels[name].configure(text=f"⏱ {hours:02}:{minutes:02}:{seconds:02}", text_color=SUCCESS)
                try:
                    process_info = psutil.Process(p.pid)
                    memory_use_mb = process_info.memory_info().rss / (1024 * 1024)
                    if name in self.ram_labels: self.ram_labels[name].configure(text=f"{memory_use_mb:.1f} MB", text_color=TEXT_SUB)
                except: pass
            else:
                if name in self.ram_labels: self.ram_labels[name].configure(text="0.0 MB", text_color="#4D4D66")
                if name in self.uptime_labels: self.uptime_labels[name].configure(text="⏱ 00:00:00", text_color="#4D4D66")

        self.after(1000, self.update_ui_loop)

if __name__ == "__main__":
    app = GalaxyDiscordManager()
    app.mainloop()