# MADE BY      _____   _____   ______   _      
#     /\      / ____| |_   _| |  ____| | |     
#    /  \    | |        | |   | |__    | |     
#   / /\ \   | |        | |   |  __|   | |     
#  / ____ \  | |____   _| |_  | |____  | |____ 
# /_/    \_\  \_____| |_____| |______| |______|

__version__ = "1.0.1"
GITHUB_API_RELEASES = (
    "https://api.github.com/repos/acieldes/MH-Morph-Manager/releases/latest"
)

import os
import sys
import csv
import json
import tempfile
import threading
import time

import requests           # pip install requests
import keyboard           # pip install keyboard
import mouse              # pip install mouse
import pyperclip          # pip install pyperclip

from pynput import keyboard as pykeyboard
from pynput import mouse as pymouse

import tkinter as tk
from tkinter import ttk, messagebox

# ─── Default Settings ───────────────────────────────────────────────────────────
ActivationKey = "x2"
WaitDuration = 0.12  # seconds

# Default Events
_Events = {
    "ActivationKey.Changed": threading.Event()
}

# Foundational Variables
_SettingAction = {
    "ActivationKeyListener": True
}

# ─── Paths & Storage Setup ─────────────────────────────────────────────────────
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if getattr(sys, 'frozen', False):
    USER_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'MH_Morph_Manager')
else:
    USER_DIR = BASE_DIR
os.makedirs(USER_DIR, exist_ok=True)

# Paths
BUNDLED_MORPHS = os.path.join(BASE_DIR, "Morphs.txt")
USER_MORPHS = os.path.join(USER_DIR, "Morphs.txt")
SETTINGS_FILE = os.path.join(USER_DIR, "settings.json")
ICON_FILE = os.path.join(BASE_DIR, "app.ico")

# On first run copy defaults
if getattr(sys, 'frozen', False) and not os.path.exists(USER_MORPHS):
    try:
        with open(BUNDLED_MORPHS, 'r', encoding='utf-8') as src, open(USER_MORPHS, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    except FileNotFoundError:
        open(USER_MORPHS, 'w', encoding='utf-8').close()

# Very Important stuff
def Event(thread: threading.Event):
    if not thread.is_set: thread.set
    thread.clear

def Connect(thread: threading.Event, func):
    def a():
        thread.wait()
        func()
    threading.Thread(target=a, daemon=True).start()

# ─── Load / Save Morphs ────────────────────────────────────────────────────────
def load_morphs():
    morphs = []
    try:
        with open(USER_MORPHS, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                morphs.append({"Name": row.get("Name", ""), "Morph": row.get("Morph", "")})
    except FileNotFoundError:
        print(f"Warning: no {USER_MORPHS} found.")
    return morphs


def save_morphs(morphs):
    with open(USER_MORPHS, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Morph"])
        writer.writeheader()
        writer.writerows(morphs)

# ─── Load / Save Settings ─────────────────────────────────────────────────────
def load_settings():
    global ActivationKey, WaitDuration
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                ActivationKey = data.get('ActivationKey', ActivationKey)
                WaitDuration = data.get('WaitDuration', WaitDuration)
        except Exception:
            pass
    else:
        save_settings()


def save_settings():
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'ActivationKey': ActivationKey, 'WaitDuration': WaitDuration}, f, indent=2)

# ─── Tooltip Helper ─────────────────────────────────────────────────────────────
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y = event.x_root + 20, event.y_root + 10
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="lightyellow", relief="solid", borderwidth=1, font=("tahoma", 8))
        label.pack()
        self.tipwindow = tw

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# ─── Update Checker ─────────────────────────────────────────────────────────────
def check_for_updates():
    try:
        resp = requests.get(GITHUB_API_RELEASES, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        latest = data["tag_name"].lstrip("v")
        if latest != __version__:
            if messagebox.askyesno("Update Available", f"New version {latest} available. Install now?" ):
                asset = data["assets"][0]["browser_download_url"]
                dest = os.path.join(tempfile.gettempdir(), os.path.basename(asset))
                with requests.get(asset, stream=True) as dl:
                    dl.raise_for_status()
                    with open(dest, "wb") as f:
                        for chunk in dl.iter_content(1024*1024): f.write(chunk)
                os.startfile(dest)
                sys.exit(0)
    except Exception as e:
        print("Update check failed:", e)

# ─── GUI Callbacks ──────────────────────────────────────────────────────────────
selected_name = None
selected_text = None

def on_morph_button(morph):
    global selected_name, selected_text
    selected_name, selected_text = morph["Name"], morph["Morph"]
    title_var.set(f"{selected_name} ({selected_text})")


def remove_morph(morph, button):
    current = [m for m in Morphs if m != morph]
    save_morphs(current)
    Morphs[:] = current
    button.destroy()
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_scrollbar()
    reset_selection(morph)


def reset_selection(morph):
    global selected_name, selected_text
    if selected_name == morph["Name"] and selected_text == morph["Morph"]:
        selected_name = selected_text = None
        title_var.set("No Morph selected.")


def show_context_menu(event, button):
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Remove", command=lambda: remove_morph(button.morph, button))
    menu.tk_popup(event.x_root, event.y_root)


def create_morph(name, morph_cmd, dialog):
    if not name or not morph_cmd: return
    with open(USER_MORPHS, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, morph_cmd])
    new = {"Name": name, "Morph": morph_cmd}
    Morphs.append(new)
    btn = ttk.Button(scrollable_frame, text=name, command=lambda m=new: on_morph_button(m))
    btn.morph = new
    btn.pack(fill="x", pady=2, expand=True)
    ToolTip(btn, morph_cmd)
    btn.bind("<Button-3>", lambda e, b=btn: show_context_menu(e, b))
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_scrollbar()
    dialog.destroy()


def open_add_window():
    win = tk.Toplevel(root)
    win.title("Add New Morph")
    win.resizable(False, False)
    win.iconbitmap(ICON_FILE)
    win.geometry(f"+{root.winfo_x()}+{root.winfo_y()}")
    ttk.Label(win, text="Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    name_entry = ttk.Entry(win); name_entry.grid(row=0, column=1, padx=5, pady=5)
    ttk.Label(win, text="Morph:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    morph_entry = ttk.Entry(win); morph_entry.grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(win, text="Create", command=lambda: create_morph(name_entry.get(), morph_entry.get(), win)).grid(row=2, column=0, columnspan=2, pady=10)
    win.grab_set(); name_entry.focus()

# ─── Scrollbar Helpers ─────────────────────────────────────────────────────────
def update_scrollbar(event=None):
    needed = scrollable_frame.winfo_reqheight() > canvas.winfo_height()
    if needed and not scrollbar.winfo_ismapped(): scrollbar.pack(side="right", fill="y")
    elif not needed and scrollbar.winfo_ismapped(): scrollbar.pack_forget()
    offset = scrollbar.winfo_width() if needed else 0
    canvas.itemconfig(window_id, width=canvas.winfo_width()-offset)


def on_mouse_wheel(event):
    top, bottom = canvas.yview()
    delta = int(-1 * (event.delta / 120))
    if (delta < 0 and top > 0) or (delta > 0 and bottom < 1):
        canvas.yview_scroll(delta, "units")

def GetKeySource(key: str): # I actually made this function myself
    """Get the source of a key, nil if none."""
    key = key.lower()
    valid_mouse_buttons = {"left", "right", "middle", "x", "x2"}
    
    try:
        keyboard.key_to_scan_codes(key); return keyboard
    except ValueError:
        if key in valid_mouse_buttons: return mouse

# ─── Settings Window ───────────────────────────────────────────────────────────
def open_settings_window():    
    win = tk.Toplevel(root)
    win.title("Settings")
    win.resizable(False, False)
    win.iconbitmap(ICON_FILE)
    win.geometry(f"+{root.winfo_x()+50}+{root.winfo_y()+50}")

    ttk.Label(win, text="Activation Keybind:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    key_var = tk.StringVar(value=ActivationKey)
    key_entry = ttk.Entry(win, textvariable=key_var)
    key_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(win, text="Wait Duration (0.1-1s):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    duration_var = tk.StringVar(value=str(WaitDuration))
    dur_entry = ttk.Entry(win, textvariable=duration_var)
    dur_entry.grid(row=1, column=1, padx=5, pady=5)

    _SettingAction["ActivationKeyListener"] = False

    def save_and_close():
        global ActivationKey, WaitDuration
        new_key = key_var.get()
        try:
            print(GetKeySource(new_key))
            
            new_wait = float(duration_var.get())
            if not 0.1 <= new_wait <= 1.0:
                raise ValueError("Wait Duration out of range")
            
            ActivationKey = new_key; Event(_Events["ActivationKey.Changed"])
            WaitDuration = new_wait
            save_settings()
            win.destroy()
        except ValueError as err:
            messagebox.showerror("Invalid Input", str(err))
        _SettingAction["ActivationKeyListener"] = True

    ttk.Button(win, text="Save", command=save_and_close).grid(row=2, column=0, columnspan=2, pady=10)
    win.grab_set()

def toggle_listener(btn):
    """Flip the listener flag and update the button’s label."""
    current = _SettingAction.get("ActivationKeyListener")
    # only flip if bool, else go to error

    _SettingAction["ActivationKeyListener"] = not _SettingAction["ActivationKeyListener"]

    if _SettingAction["ActivationKeyListener"] is True:
        label = "State: Enabled"
    elif _SettingAction["ActivationKeyListener"] is False:
        label = "State: Disabled"
    else:
        label = "State: Error"

    btn.config(text=label)

# ─── Activation Listener ───────────────────────────────────────────────────────
def listen_activation():
    def main_action():
        if selected_text:
            keyboard.press_and_release(";")
            pyperclip.copy(selected_text)
            time.sleep(WaitDuration)
            keyboard.press_and_release("ctrl+v")
            time.sleep(WaitDuration)
            keyboard.press_and_release("enter")

    def mouse_action(x, y, key:pymouse.Button, pressed, injected):
        if not _SettingAction["ActivationKeyListener"] is True: return

        if injected: return
        if not pressed: return
        
        try:
            if key.name == ActivationKey: main_action()
        except AttributeError: return

    def keyboard_action(key:pykeyboard.KeyCode, injected):
        if not _SettingAction["ActivationKeyListener"] is True: return

        if injected: return
        
        try:
            if key.char == ActivationKey: main_action()
        except AttributeError: return

    pymouse.Listener(
        on_click=mouse_action
    ).start()

    pykeyboard.Listener(
        on_press=keyboard_action
    ).start()

# ─── Main GUI Setup ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Morphs = load_morphs()
    load_settings()
    check_for_updates()

    root = tk.Tk()
    root.title("MH Morph Manager")
    root.iconbitmap(ICON_FILE)
    root.minsize(300, 300)
    root.maxsize(500, 600)

    # Title above scroll only
    title_var = tk.StringVar(value="No Morph selected.")
    title_label = ttk.Label(root, textvariable=title_var, font=("Segoe UI", 12))
    title_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")

    # Scroll area in row1, col0
    container = ttk.Frame(root)
    container.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
    canvas = tk.Canvas(container, height=200, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=lambda *args: canvas.yview(*args))
    scrollable_frame = tk.Frame(canvas)
    window_id = canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    scrollable_frame.bind("<Configure>", lambda e: (canvas.configure(scrollregion=canvas.bbox("all")), update_scrollbar()))
    canvas.bind("<Configure>", update_scrollbar)
    canvas.bind_all("<MouseWheel>", on_mouse_wheel)
    canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
    canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

    # Populate morph buttons
    for morph in Morphs:
        btn = ttk.Button(scrollable_frame, text=morph["Name"], command=lambda m=morph: on_morph_button(m))
        btn.morph = morph
        btn.pack(fill="x", pady=2, expand=True)
        ToolTip(btn, morph["Morph"])
        btn.bind("<Button-3>", lambda e, b=btn: show_context_menu(e, b))

    # Side buttons next to scroll
    side_frame = ttk.Frame(root)
    side_frame.grid(row=1, column=1, padx=(0,10), pady=5, sticky="n")
    ttk.Button(side_frame, text="Add Morph", command=open_add_window).pack(fill="x", pady=2)
    ttk.Button(side_frame, text="Settings", command=open_settings_window).pack(fill="x", pady=2)

    # compute initial label
    init = _SettingAction.get("ActivationKeyListener")
    init_label = "State: Enabled" if init is True else "State: Disabled" if init is False else "State: Error"
    state_btn = ttk.Button(side_frame, text=init_label)
    state_btn.pack(fill="x", pady=2)

    # wire up toggle_listener, passing the button itself
    state_btn.config(command=lambda b=state_btn: toggle_listener(b))

    # Configure grid weights
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    threading.Thread(target=listen_activation, daemon=True).start()
    root.mainloop()