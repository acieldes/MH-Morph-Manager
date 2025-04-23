# MADE BY      _____   _____   ______   _      
#     /\      / ____| |_   _| |  ____| | |     
#    /  \    | |        | |   | |__    | |     
#   / /\ \   | |        | |   |  __|   | |     
#  / ____ \  | |____   _| |_  | |____  | |____ 
# /_/    \_\  \_____| |_____| |______| |______|

__version__ = "1.0.0"
GITHUB_API_RELEASES = "https://api.github.com/repos/acieldes/MH-Morph-Manager/releases/latest"

import os
import csv
import tkinter as tk
from tkinter import ttk
import threading
import time
import keyboard    # pip install keyboard # type: ignore
import pyperclip   # pip install pyperclip # type: ignore
import mouse      # pip install mouse     # type: ignore
import requests, sys, os, tempfile, webbrowser
from tkinter import messagebox

# —— File paths & Load Morphs —— #
script_dir = os.path.dirname(os.path.abspath(__file__))
morphs_path = os.path.join(script_dir, "Morphs.txt")
icon_path = os.path.join(script_dir, "app.ico")

Morphs = []
try:
    with open(morphs_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'Name' in row and 'Morph' in row:
                Morphs.append({'Name': row['Name'], 'Morph': row['Morph']})
except FileNotFoundError:
    print(f"Morphs.txt not found at {morphs_path}")

# —— Config —— #
ActivationKey = 'x2'

# —— Auto-Update —— #
def check_for_updates():
    try:
        r = requests.get(GITHUB_API_RELEASES, timeout=5)
        r.raise_for_status()
        data = r.json()
        latest = data["tag_name"].lstrip("v")
        if latest != __version__:
            if messagebox.askyesno(
                  "Update available",
                  f"A new version ({latest}) is available.\nDownload and install?"
               ):
                # assume your .exe is the first asset:
                url = data["assets"][0]["browser_download_url"]
                dlpath = os.path.join(tempfile.gettempdir(), os.path.basename(url))
                with requests.get(url, stream=True) as dl:
                    dl.raise_for_status()
                    with open(dlpath, "wb") as f:
                        for chunk in dl.iter_content(1024*1024):
                            f.write(chunk)
                # launch installer/exe and quit:
                os.startfile(dlpath)
                sys.exit(0)
    except Exception as e:
        print("Update check failed:", e)

# —— Tooltip Helper —— #
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
        x = event.x_root + 20; y = event.y_root + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="lightyellow",
                         relief="solid", borderwidth=1, font=("tahoma",8))
        label.pack()

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy(); self.tipwindow = None

# —— State & Callbacks —— #
selected_name = None
selected_text = None

# GUI command: select morph
def on_morph_button(morph):
    global selected_name, selected_text
    selected_name, selected_text = morph['Name'], morph['Morph']
    title_var.set(f"{selected_name} ({selected_text})")

# Remove morph: update file, list, and GUI
def remove_morph(morph, btn):
    # Remove from file
    try:
        # Read all rows
        with open(morphs_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [r for r in reader if not (r['Name']==morph['Name'] and r['Morph']==morph['Morph'])]
        # Write back header + rows
        with open(morphs_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['Name','Morph'])
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        print("Error updating Morphs.txt:", e)
    # Remove from in-memory and GUI
    if morph in Morphs: Morphs.remove(morph)
    btn.destroy()
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_scrollbar_visibility()
    # Clear selection if needed
    global selected_name, selected_text
    if selected_name==morph['Name'] and selected_text==morph['Morph']:
        selected_name = selected_text = None
        title_var.set("No Morph is selected.")

# Context menu popup
def show_context_menu(event, btn):
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Remove", command=lambda: remove_morph(btn.morph, btn))
    menu.tk_popup(event.x_root, event.y_root)

# Add new morph to file and UI
def create_morph(name, morph_cmd, window):
    if not name or not morph_cmd: return
    try:
        # Ensure newline before append
        with open(morphs_path,'rb+') as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) not in (b'\n',b'\r'): f.write(b'\n')
        with open(morphs_path,'a',newline='',encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([name, morph_cmd])
    except Exception as e:
        print("Error writing Morphs.txt:", e)
    new_m = {'Name':name,'Morph':morph_cmd}
    Morphs.append(new_m)
    btn = ttk.Button(scrollable_frame, text=name, command=lambda m=new_m: on_morph_button(m))
    btn.morph = new_m
    btn.pack(fill="x", pady=2, expand=True)
    ToolTip(btn, morph_cmd)
    btn.bind('<Button-3>', lambda e,b=btn: show_context_menu(e,b))
    canvas.configure(scrollregion=canvas.bbox("all")); update_scrollbar_visibility()
    window.destroy()

root = tk.Tk(); root.title("MH Morphing"); root.minsize(300,300); root.maxsize(300,600); root.iconbitmap(icon_path)

# Open dialog to add morph
def open_add_window():
    win = tk.Toplevel(root); win.title("Add New Morph"); win.resizable(False,False)
    win.geometry(f"+{root.winfo_x()}+{root.winfo_y()}")
    ttk.Label(win, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    name_entry = ttk.Entry(win); name_entry.grid(row=0, column=1, padx=5, pady=5)
    ttk.Label(win, text="Morph:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    morph_entry = ttk.Entry(win); morph_entry.grid(row=1, column=1, padx=5, pady=5)
    create_btn = ttk.Button(win, text="Create",
        command=lambda: create_morph(name_entry.get(), morph_entry.get(), win))
    create_btn.grid(row=2, column=0, columnspan=2, pady=10)
    win.grab_set(); win.focus(); win.iconbitmap(icon_path)

if __name__ == "__main__":
    check_for_updates()

# —— GUI Setup —— Title
title_var = tk.StringVar(value="No Morph is selected.")
title_label = ttk.Label(root, textvariable=title_var, font=("Segoe UI",12))
title_label.pack(pady=(10,5))
# Scroll area
container = ttk.Frame(root); container.pack(fill="both",expand=True,padx=10,pady=5)
canvas = tk.Canvas(container, height=200, highlightthickness=0, bd=0)
scrollbar = ttk.Scrollbar(container, orient="vertical")
scrollable_frame = tk.Frame(canvas)
window_id = canvas.create_window((0,0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set); scrollbar.configure(command=canvas.yview)
canvas.pack(side="left",fill="both",expand=True); scrollbar.pack(side="right",fill="y")
# Scrollbar visibility & width adjust
def update_scrollbar_visibility(event=None):
    req_h = scrollable_frame.winfo_reqheight(); cur_h = canvas.winfo_height()
    if req_h>cur_h and not scrollbar.winfo_ismapped(): scrollbar.pack(side="right",fill="y")
    if req_h<=cur_h and scrollbar.winfo_ismapped(): scrollbar.pack_forget()
    sb = scrollbar.winfo_width() if scrollbar.winfo_ismapped() else 0
    canvas.itemconfig(window_id, width=canvas.winfo_width()-sb)
scrollable_frame.bind("<Configure>", lambda e: (canvas.configure(scrollregion=canvas.bbox("all")), update_scrollbar_visibility()))
canvas.bind('<Configure>',update_scrollbar_visibility)
# Mouse wheel
canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units") if 0<canvas.yview()[0]<1 else None)
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1,"units") if canvas.yview()[0]>0 else None)
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1,"units") if canvas.yview()[1]<1 else None)
# Populate buttons
for m in Morphs:
    btn = ttk.Button(scrollable_frame, text=m['Name'], command=lambda x=m: on_morph_button(x))
    btn.morph = m
    btn.pack(fill="x",pady=2,expand=True)
    ToolTip(btn,m['Morph'])
    btn.bind('<Button-3>', lambda e,b=btn: show_context_menu(e,b))
# Add Morph button
add_btn = ttk.Button(root, text="Add Morph", command=open_add_window)
add_btn.pack(pady=5)
# Activation listener
def listen_activation():
    while True:
        mouse.wait(button=ActivationKey)
        if selected_text:
            keyboard.press_and_release(';'); time.sleep(0.1)
            pyperclip.copy(selected_text); keyboard.press_and_release('ctrl+v')
            time.sleep(0.1); keyboard.press_and_release('enter')
threading.Thread(target=listen_activation, daemon=True).start()
root.mainloop()