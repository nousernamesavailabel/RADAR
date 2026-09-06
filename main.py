
#!/usr/bin/env python3

import concurrent.futures
import csv
import ctypes
import ipaddress
import os
import platform
import shutil
import subprocess
import threading
import time
import tkinter as tk
import webbrowser
import winreg
from tkinter import ttk, messagebox, filedialog


APP_NAME = "RADAR"
APP_VERSION = "1.2"
APP_FULL_NAME = "Rapid Address Discovery And Response"


class RadarApp:
    def __init__(self, root):
        self.root = root

        self.root.title(
            f"{APP_NAME} - {APP_FULL_NAME}"
        )

        self.root.geometry("920x720")
        self.root.minsize(820, 620)

        # -------------------------------------------------
        # Colors
        # -------------------------------------------------
        self.bg = "#11161c"
        self.panel = "#1a2129"
        self.panel_alt = "#202932"
        self.text = "#e6edf3"
        self.muted = "#8b98a5"
        self.accent = "#35f28b"
        self.accent_dim = "#237a50"
        self.border = "#303a44"

        self.root.configure(
            bg=self.bg
        )

        # -------------------------------------------------
        # Scan state
        # -------------------------------------------------
        self.stop_event = threading.Event()
        self.scan_thread = None
        self.alive_hosts = []

        self.configure_styles()
        self.build_gui()

    # =====================================================
    # Styling
    # =====================================================
    def configure_styles(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Radar.TFrame",
            background=self.bg
        )

        style.configure(
            "Panel.TFrame",
            background=self.panel
        )

        style.configure(
            "Radar.TButton",
            padding=(14, 7),
            background=self.panel_alt,
            foreground=self.text,
            borderwidth=1
        )

        style.map(
            "Radar.TButton",
            background=[
                ("active", "#2b3641"),
                ("disabled", "#171c22")
            ],
            foreground=[
                ("disabled", "#5e6872")
            ]
        )

        style.configure(
            "Accent.TButton",
            padding=(16, 7),
            background=self.accent,
            foreground="#08120d",
            borderwidth=0
        )

        style.map(
            "Accent.TButton",
            background=[
                ("active", "#6cffad"),
                ("disabled", "#244d38")
            ],
            foreground=[
                ("disabled", "#7b9184")
            ]
        )

        style.configure(
            "Radar.TEntry",
            fieldbackground="#0d1217",
            foreground=self.text,
            insertcolor=self.text,
            bordercolor=self.border
        )

        style.configure(
            "Radar.TSpinbox",
            fieldbackground="#0d1217",
            foreground=self.text,
            arrowcolor=self.text,
            bordercolor=self.border
        )

        style.configure(
            "Radar.Horizontal.TProgressbar",
            troughcolor="#0d1217",
            background=self.accent,
            bordercolor=self.border,
            lightcolor=self.accent,
            darkcolor=self.accent,
            thickness=18
        )

    # =====================================================
    # GUI
    # =====================================================
    def build_gui(self):
        main = ttk.Frame(
            self.root,
            style="Radar.TFrame",
            padding=20
        )

        main.pack(
            fill="both",
            expand=True
        )

        self.build_header(main)
        self.build_scan_panel(main)
        self.build_progress_panel(main)
        self.build_results_panel(main)

    # =====================================================
    # Header
    # =====================================================
    def build_header(self, parent):
        header = ttk.Frame(
            parent,
            style="Radar.TFrame"
        )

        header.pack(
            fill="x",
            pady=(0, 18)
        )

        logo = tk.Canvas(
            header,
            width=74,
            height=74,
            bg=self.bg,
            highlightthickness=0
        )

        logo.pack(
            side="left",
            padx=(0, 15)
        )

        self.draw_radar_logo(logo)

        title_frame = ttk.Frame(
            header,
            style="Radar.TFrame"
        )

        title_frame.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            title_frame,
            text="RADAR",
            font=("Segoe UI", 25, "bold"),
            bg=self.bg,
            fg=self.accent
        ).pack(
            anchor="w"
        )

        tk.Label(
            title_frame,
            text=APP_FULL_NAME,
            font=("Segoe UI", 11),
            bg=self.bg,
            fg=self.text
        ).pack(
            anchor="w"
        )

        tk.Label(
            title_frame,
            text="Find what's alive. Get to it fast.",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted
        ).pack(
            anchor="w",
            pady=(2, 0)
        )

        right_frame = ttk.Frame(
            header,
            style="Radar.TFrame"
        )

        right_frame.pack(
            side="right",
            anchor="n"
        )

        tk.Label(
            right_frame,
            text=f"v{APP_VERSION}",
            font=("Consolas", 9),
            bg=self.bg,
            fg=self.muted
        ).pack(
            anchor="e",
            pady=(0, 8)
        )

        ttk.Button(
            right_frame,
            text="HELP",
            command=self.open_help,
            style="Radar.TButton"
        ).pack(
            anchor="e"
        )

    def draw_radar_logo(self, canvas):
        cx = 37
        cy = 37

        for radius in (30, 21, 12):
            canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                outline=self.accent_dim,
                width=1
            )

        canvas.create_line(
            cx,
            6,
            cx,
            68,
            fill=self.accent_dim
        )

        canvas.create_line(
            6,
            cy,
            68,
            cy,
            fill=self.accent_dim
        )

        canvas.create_line(
            cx,
            cy,
            60,
            17,
            fill=self.accent,
            width=2
        )

        for x, y in (
            (53, 27),
            (26, 20),
            (49, 50)
        ):
            canvas.create_oval(
                x - 2,
                y - 2,
                x + 2,
                y + 2,
                fill=self.accent,
                outline=self.accent
            )

        canvas.create_oval(
            cx - 2,
            cy - 2,
            cx + 2,
            cy + 2,
            fill=self.accent,
            outline=self.accent
        )

    # =====================================================
    # Scan Panel
    # =====================================================
    def build_scan_panel(self, parent):
        outer = tk.Frame(
            parent,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

        outer.pack(
            fill="x",
            pady=(0, 12)
        )

        panel = ttk.Frame(
            outer,
            style="Panel.TFrame",
            padding=15
        )

        panel.pack(
            fill="x"
        )

        tk.Label(
            panel,
            text="NETWORK SWEEP",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.accent
        ).grid(
            row=0,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(0, 10)
        )

        tk.Label(
            panel,
            text="Subnet",
            bg=self.panel,
            fg=self.muted
        ).grid(
            row=1,
            column=0,
            sticky="w",
            padx=(0, 6)
        )

        self.subnet_var = tk.StringVar(
            value="192.168.1.0/24"
        )

        self.subnet_entry = ttk.Entry(
            panel,
            textvariable=self.subnet_var,
            width=25,
            style="Radar.TEntry"
        )

        self.subnet_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(0, 15)
        )

        tk.Label(
            panel,
            text="Workers",
            bg=self.panel,
            fg=self.muted
        ).grid(
            row=1,
            column=2,
            sticky="w",
            padx=(0, 6)
        )

        self.workers_var = tk.IntVar(
            value=100
        )

        self.workers_spin = ttk.Spinbox(
            panel,
            from_=1,
            to=1000,
            width=7,
            textvariable=self.workers_var,
            style="Radar.TSpinbox"
        )

        self.workers_spin.grid(
            row=1,
            column=3,
            padx=(0, 15)
        )

        tk.Label(
            panel,
            text="Timeout",
            bg=self.panel,
            fg=self.muted
        ).grid(
            row=1,
            column=4,
            sticky="w",
            padx=(0, 6)
        )

        self.timeout_var = tk.DoubleVar(
            value=1.0
        )

        self.timeout_spin = ttk.Spinbox(
            panel,
            from_=0.1,
            to=10,
            increment=0.1,
            width=7,
            textvariable=self.timeout_var,
            style="Radar.TSpinbox"
        )

        self.timeout_spin.grid(
            row=1,
            column=5
        )

        panel.columnconfigure(
            1,
            weight=1
        )

        controls = ttk.Frame(
            panel,
            style="Panel.TFrame"
        )

        controls.grid(
            row=2,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(14, 0)
        )

        self.scan_button = ttk.Button(
            controls,
            text="SCAN NETWORK",
            command=self.start_scan,
            style="Accent.TButton"
        )

        self.scan_button.pack(
            side="left",
            padx=(0, 7)
        )

        self.stop_button = ttk.Button(
            controls,
            text="STOP",
            command=self.stop_scan,
            style="Radar.TButton",
            state="disabled"
        )

        self.stop_button.pack(
            side="left",
            padx=7
        )

        self.clear_button = ttk.Button(
            controls,
            text="CLEAR RESULTS",
            command=self.clear_results,
            style="Radar.TButton"
        )

        self.clear_button.pack(
            side="left",
            padx=7
        )

        self.copy_button = ttk.Button(
            controls,
            text="COPY IPs",
            command=self.copy_results,
            style="Radar.TButton"
        )

        self.copy_button.pack(
            side="left",
            padx=7
        )

        self.export_button = ttk.Button(
            controls,
            text="EXPORT",
            command=self.export_csv,
            style="Radar.TButton"
        )

        self.export_button.pack(
            side="left",
            padx=7
        )

    # =====================================================
    # Progress Panel
    # =====================================================
    def build_progress_panel(self, parent):
        outer = tk.Frame(
            parent,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

        outer.pack(
            fill="x",
            pady=(0, 12)
        )

        panel = tk.Frame(
            outer,
            bg=self.panel
        )

        panel.pack(
            fill="x",
            padx=15,
            pady=12
        )

        top = tk.Frame(
            panel,
            bg=self.panel
        )

        top.pack(
            fill="x",
            pady=(0, 8)
        )

        tk.Label(
            top,
            text="SWEEP PROGRESS",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.accent
        ).pack(
            side="left"
        )

        self.percent_var = tk.StringVar(
            value="0%"
        )

        tk.Label(
            top,
            textvariable=self.percent_var,
            font=("Consolas", 11, "bold"),
            bg=self.panel,
            fg=self.text
        ).pack(
            side="right"
        )

        self.progress = ttk.Progressbar(
            panel,
            mode="determinate",
            style="Radar.Horizontal.TProgressbar"
        )

        self.progress.pack(
            fill="x",
            pady=(0, 8)
        )

        stats = tk.Frame(
            panel,
            bg=self.panel
        )

        stats.pack(
            fill="x"
        )

        self.scan_count_var = tk.StringVar(
            value="0 / 0 scanned"
        )

        tk.Label(
            stats,
            textvariable=self.scan_count_var,
            font=("Consolas", 10),
            bg=self.panel,
            fg=self.text
        ).pack(
            side="left"
        )

        self.progress_hosts_var = tk.StringVar(
            value="0 hosts discovered"
        )

        tk.Label(
            stats,
            textvariable=self.progress_hosts_var,
            font=("Consolas", 10),
            bg=self.panel,
            fg=self.accent
        ).pack(
            side="right"
        )

        self.status_var = tk.StringVar(
            value="RADAR ready."
        )

        tk.Label(
            panel,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=self.panel,
            fg=self.muted
        ).pack(
            anchor="w",
            pady=(7, 0)
        )

    # =====================================================
    # Results Panel
    # =====================================================
    def build_results_panel(self, parent):
        outer = tk.Frame(
            parent,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

        outer.pack(
            fill="both",
            expand=True
        )

        header = tk.Frame(
            outer,
            bg=self.panel
        )

        header.pack(
            fill="x",
            padx=15,
            pady=(12, 6)
        )

        tk.Label(
            header,
            text="DISCOVERED HOSTS",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.accent
        ).pack(
            side="left"
        )

        self.host_count_var = tk.StringVar(
            value="0 ONLINE"
        )

        tk.Label(
            header,
            textvariable=self.host_count_var,
            font=("Consolas", 9),
            bg=self.panel,
            fg=self.muted
        ).pack(
            side="right"
        )

        table_header = tk.Frame(
            outer,
            bg=self.panel_alt
        )

        table_header.pack(
            fill="x",
            padx=15
        )

        tk.Label(
            table_header,
            text="IP ADDRESS",
            width=28,
            anchor="w",
            font=("Consolas", 9, "bold"),
            bg=self.panel_alt,
            fg=self.muted,
            padx=10,
            pady=7
        ).pack(
            side="left"
        )

        tk.Label(
            table_header,
            text="STATUS",
            width=14,
            anchor="w",
            font=("Consolas", 9, "bold"),
            bg=self.panel_alt,
            fg=self.muted,
            padx=5,
            pady=7
        ).pack(
            side="left"
        )

        tk.Label(
            table_header,
            text="ACTIONS",
            anchor="w",
            font=("Consolas", 9, "bold"),
            bg=self.panel_alt,
            fg=self.muted,
            padx=5,
            pady=7
        ).pack(
            side="left"
        )

        result_area = tk.Frame(
            outer,
            bg=self.panel
        )

        result_area.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        self.canvas = tk.Canvas(
            result_area,
            bg=self.panel,
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            result_area,
            orient="vertical",
            command=self.canvas.yview
        )

        self.results_container = tk.Frame(
            self.canvas,
            bg=self.panel
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.results_container,
            anchor="nw"
        )

        self.results_container.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_results_container
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

    def resize_results_container(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    # =====================================================
    # HELP
    # =====================================================
    def open_help(self):
        help_window = tk.Toplevel(
            self.root
        )

        help_window.title(
            "RADAR Help"
        )

        help_window.geometry(
            "620x470"
        )

        help_window.resizable(
            False,
            False
        )

        help_window.configure(
            bg=self.bg
        )

        help_window.transient(
            self.root
        )

        help_window.grab_set()

        header = tk.Frame(
            help_window,
            bg=self.bg
        )

        header.pack(
            fill="x",
            padx=20,
            pady=(20, 15)
        )

        tk.Label(
            header,
            text="RADAR HELP",
            font=("Segoe UI", 20, "bold"),
            bg=self.bg,
            fg=self.accent
        ).pack(
            anchor="w"
        )

        tk.Label(
            header,
            text=f"{APP_FULL_NAME}  |  v{APP_VERSION}",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

        info_panel = tk.Frame(
            help_window,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

        info_panel.pack(
            fill="x",
            padx=20,
            pady=(0, 12)
        )

        tk.Label(
            info_panel,
            text="USING RADAR",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.accent
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 6)
        )

        instructions = (
            "1. Enter a subnet in CIDR notation, such as 192.168.1.0/24.\n"
            "2. Select SCAN NETWORK to begin the ICMP sweep.\n"
            "3. Hosts responding to ICMP appear under DISCOVERED HOSTS.\n"
            "4. SSH launches PuTTY for the selected host.\n"
            "5. WEB opens https://<host> in your default browser."
        )

        tk.Label(
            info_panel,
            text=instructions,
            justify="left",
            font=("Segoe UI", 9),
            bg=self.panel,
            fg=self.text
        ).pack(
            anchor="w",
            padx=15,
            pady=(0, 12)
        )

        tools_panel = tk.Frame(
            help_window,
            bg=self.panel,
            highlightbackground=self.border,
            highlightthickness=1
        )

        tools_panel.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20)
        )

        tk.Label(
            tools_panel,
            text="WINDOWS INTEGRATION",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.accent
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 8)
        )

        # -------------------------------------------------
        # Default Apps
        # -------------------------------------------------
        default_frame = tk.Frame(
            tools_panel,
            bg=self.panel
        )

        default_frame.pack(
            fill="x",
            padx=15,
            pady=(0, 12)
        )

        default_text = tk.Frame(
            default_frame,
            bg=self.panel
        )

        default_text.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            default_text,
            text="Windows Default Apps",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.text
        ).pack(
            anchor="w"
        )

        tk.Label(
            default_text,
            text="Change the browser used by RADAR's WEB button.",
            font=("Segoe UI", 9),
            bg=self.panel,
            fg=self.muted
        ).pack(
            anchor="w"
        )

        ttk.Button(
            default_frame,
            text="OPEN DEFAULT APPS",
            command=self.open_default_apps,
            style="Radar.TButton"
        ).pack(
            side="right"
        )

        separator = tk.Frame(
            tools_panel,
            height=1,
            bg=self.border
        )

        separator.pack(
            fill="x",
            padx=15,
            pady=4
        )

        # -------------------------------------------------
        # PuTTY PATH
        # -------------------------------------------------
        putty_frame = tk.Frame(
            tools_panel,
            bg=self.panel
        )

        putty_frame.pack(
            fill="x",
            padx=15,
            pady=(10, 8)
        )

        putty_text = tk.Frame(
            putty_frame,
            bg=self.panel
        )

        putty_text.pack(
            side="left",
            fill="x",
            expand=True
        )

        tk.Label(
            putty_text,
            text="PuTTY Integration",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel,
            fg=self.text
        ).pack(
            anchor="w"
        )

        self.help_putty_status = tk.StringVar()

        tk.Label(
            putty_text,
            textvariable=self.help_putty_status,
            font=("Segoe UI", 9),
            bg=self.panel,
            fg=self.muted
        ).pack(
            anchor="w"
        )

        ttk.Button(
            putty_frame,
            text="ADD PuTTY TO PATH",
            command=self.add_putty_to_path,
            style="Radar.TButton"
        ).pack(
            side="right"
        )

        self.update_putty_help_status()

    def open_default_apps(self):
        if platform.system().lower() != "windows":
            messagebox.showerror(
                "Windows Required",
                "Default Apps integration is available on Windows."
            )
            return

        try:
            os.startfile(
                "ms-settings:defaultapps"
            )

        except OSError as error:
            messagebox.showerror(
                "Default Apps",
                f"Could not open Windows Default Apps.\n\n{error}"
            )

    # =====================================================
    # PuTTY Detection
    # =====================================================
    def get_putty_locations(self):
        locations = [
            r"C:\Program Files\PuTTY\putty.exe",
            r"C:\Program Files (x86)\PuTTY\putty.exe",
            os.path.expandvars(
                r"%LOCALAPPDATA%\Programs\PuTTY\putty.exe"
            ),
            os.path.expandvars(
                r"%LOCALAPPDATA%\PuTTY\putty.exe"
            )
        ]

        return locations

    def find_putty(self):
        # Check current process PATH first.
        putty = shutil.which(
            "putty.exe"
        )

        if putty:
            return putty

        # Then check common install locations.
        for path in self.get_putty_locations():
            if os.path.isfile(path):
                return path

        return None

    def update_putty_help_status(self):
        if not hasattr(
            self,
            "help_putty_status"
        ):
            return

        putty_path = self.find_putty()

        if putty_path:
            self.help_putty_status.set(
                f"PuTTY detected: {putty_path}"
            )

        else:
            self.help_putty_status.set(
                "PuTTY was not detected in PATH or a common installation location."
            )

    # =====================================================
    # Add PuTTY to User PATH
    # =====================================================
    def add_putty_to_path(self):
        if platform.system().lower() != "windows":
            messagebox.showerror(
                "Windows Required",
                "PATH integration is currently available on Windows."
            )
            return

        putty_path = None

        # Prefer an actual installation path instead of a
        # PATH lookup because we need the containing directory.
        for path in self.get_putty_locations():
            if os.path.isfile(path):
                putty_path = path
                break

        # If PuTTY is already reachable through PATH, use it.
        if not putty_path:
            detected = shutil.which(
                "putty.exe"
            )

            if detected:
                putty_path = detected

        if not putty_path:
            messagebox.showerror(
                "PuTTY Not Found",
                "RADAR could not locate PuTTY.\n\n"
                "Install PuTTY first, then select this option again."
            )
            return

        putty_directory = os.path.dirname(
            os.path.abspath(putty_path)
        )

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment",
                0,
                winreg.KEY_READ | winreg.KEY_WRITE
            )

            try:
                current_path, value_type = (
                    winreg.QueryValueEx(
                        key,
                        "Path"
                    )
                )

            except FileNotFoundError:
                current_path = ""
                value_type = winreg.REG_EXPAND_SZ

            path_entries = [
                entry.strip()
                for entry in current_path.split(";")
                if entry.strip()
            ]

            normalized_existing = {
                os.path.normcase(
                    os.path.normpath(
                        os.path.expandvars(entry)
                    )
                )
                for entry in path_entries
            }

            normalized_putty = os.path.normcase(
                os.path.normpath(
                    putty_directory
                )
            )

            if normalized_putty in normalized_existing:
                winreg.CloseKey(
                    key
                )

                self.add_directory_to_process_path(
                    putty_directory
                )

                self.update_putty_help_status()

                messagebox.showinfo(
                    "PuTTY PATH",
                    f"PuTTY is already in your user PATH.\n\n"
                    f"{putty_directory}"
                )
                return

            if current_path and not current_path.endswith(";"):
                new_path = (
                    current_path
                    + ";"
                    + putty_directory
                )
            elif current_path:
                new_path = (
                    current_path
                    + putty_directory
                )
            else:
                new_path = putty_directory

            winreg.SetValueEx(
                key,
                "Path",
                0,
                value_type,
                new_path
            )

            winreg.CloseKey(
                key
            )

            # Make PuTTY immediately available to this
            # running RADAR process.
            self.add_directory_to_process_path(
                putty_directory
            )

            # Tell Windows that environment variables changed.
            self.broadcast_environment_change()

            self.update_putty_help_status()

            self.status_var.set(
                "PuTTY added to user PATH"
            )

            messagebox.showinfo(
                "PuTTY Added to PATH",
                f"PuTTY was added to your user PATH:\n\n"
                f"{putty_directory}\n\n"
                "RADAR can use it immediately.\n\n"
                "Other applications or command prompts that are already "
                "open may need to be restarted before they see the updated PATH."
            )

        except OSError as error:
            messagebox.showerror(
                "PATH Update Failed",
                f"RADAR could not update your user PATH.\n\n{error}"
            )

    def add_directory_to_process_path(
        self,
        directory
    ):
        current_entries = os.environ.get(
            "PATH",
            ""
        ).split(
            os.pathsep
        )

        normalized_entries = {
            os.path.normcase(
                os.path.normpath(entry)
            )
            for entry in current_entries
            if entry
        }

        normalized_directory = os.path.normcase(
            os.path.normpath(
                directory
            )
        )

        if normalized_directory not in normalized_entries:
            os.environ["PATH"] = (
                directory
                + os.pathsep
                + os.environ.get(
                    "PATH",
                    ""
                )
            )

    def broadcast_environment_change(self):
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002

        try:
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_SETTINGCHANGE,
                0,
                "Environment",
                SMTO_ABORTIFHUNG,
                5000,
                None
            )

        except Exception:
            # PATH was still successfully written to the
            # user's environment even if notification fails.
            pass

    # =====================================================
    # Start Scan
    # =====================================================
    def start_scan(self):
        if (
            self.scan_thread
            and self.scan_thread.is_alive()
        ):
            return

        subnet = self.subnet_var.get().strip()

        try:
            network = ipaddress.ip_network(
                subnet,
                strict=False
            )

        except ValueError as error:
            messagebox.showerror(
                "Invalid Subnet",
                str(error)
            )
            return

        try:
            workers = int(
                self.workers_var.get()
            )

            timeout = float(
                self.timeout_var.get()
            )

        except ValueError:
            messagebox.showerror(
                "Invalid Settings",
                "Workers and timeout must be numeric."
            )
            return

        if workers < 1:
            messagebox.showerror(
                "Invalid Workers",
                "Workers must be at least 1."
            )
            return

        if timeout <= 0:
            messagebox.showerror(
                "Invalid Timeout",
                "Timeout must be greater than 0."
            )
            return

        hosts = list(
            network.hosts()
        )

        if not hosts:
            messagebox.showerror(
                "No Hosts",
                "The selected subnet contains no usable host addresses."
            )
            return

        if len(hosts) > 65536:
            answer = messagebox.askyesno(
                "Large Sweep",
                f"This network contains "
                f"{len(hosts):,} addresses.\n\n"
                "Continue with the sweep?"
            )

            if not answer:
                return

        self.clear_results()

        self.stop_event.clear()

        self.scan_button.config(
            state="disabled"
        )

        self.stop_button.config(
            state="normal"
        )

        total = len(
            hosts
        )

        self.progress["maximum"] = total
        self.progress["value"] = 0

        self.percent_var.set(
            "0%"
        )

        self.scan_count_var.set(
            f"0 / {total:,} scanned"
        )

        self.progress_hosts_var.set(
            "0 hosts discovered"
        )

        self.status_var.set(
            f"RADAR sweep in progress | {network}"
        )

        self.scan_thread = threading.Thread(
            target=self.scan_network,
            args=(
                hosts,
                workers,
                timeout
            ),
            daemon=True
        )

        self.scan_thread.start()

    # =====================================================
    # Scan Network
    # =====================================================
    def scan_network(
        self,
        hosts,
        workers,
        timeout
    ):
        start_time = time.perf_counter()

        completed = 0

        executor = (
            concurrent.futures
            .ThreadPoolExecutor(
                max_workers=workers
            )
        )

        try:
            futures = {
                executor.submit(
                    self.ping_host,
                    ip,
                    timeout
                ): ip
                for ip in hosts
            }

            for future in (
                concurrent.futures
                .as_completed(futures)
            ):
                if self.stop_event.is_set():
                    break

                completed += 1

                try:
                    result = future.result()

                except Exception:
                    result = None

                if result:
                    ip_obj = ipaddress.ip_address(
                        result
                    )

                    self.alive_hosts.append(
                        ip_obj
                    )

                    self.root.after(
                        0,
                        self.refresh_results
                    )

                self.root.after(
                    0,
                    self.update_progress,
                    completed,
                    len(hosts)
                )

        finally:
            if self.stop_event.is_set():
                executor.shutdown(
                    wait=False,
                    cancel_futures=True
                )

            else:
                executor.shutdown(
                    wait=True
                )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        self.root.after(
            0,
            self.scan_finished,
            elapsed
        )

    # =====================================================
    # Ping
    # =====================================================
    def ping_host(
        self,
        ip,
        timeout
    ):
        if self.stop_event.is_set():
            return None

        system = platform.system().lower()

        if system == "windows":
            command = [
                "ping",
                "-n",
                "1",
                "-w",
                str(
                    int(timeout * 1000)
                ),
                str(ip)
            ]

        else:
            command = [
                "ping",
                "-c",
                "1",
                "-W",
                str(
                    max(
                        1,
                        int(timeout)
                    )
                ),
                str(ip)
            ]

        startupinfo = None

        if system == "windows":
            startupinfo = (
                subprocess.STARTUPINFO()
            )

            startupinfo.dwFlags |= (
                subprocess.STARTF_USESHOWWINDOW
            )

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout + 1,
                startupinfo=startupinfo
            )

            if result.returncode == 0:
                return str(ip)

        except (
            subprocess.TimeoutExpired,
            OSError
        ):
            pass

        return None

    # =====================================================
    # Progress
    # =====================================================
    def update_progress(
        self,
        completed,
        total
    ):
        self.progress["value"] = completed

        percentage = (
            (completed / total) * 100
            if total
            else 0
        )

        found = len(
            self.alive_hosts
        )

        self.percent_var.set(
            f"{percentage:.0f}%"
        )

        self.scan_count_var.set(
            f"{completed:,} / {total:,} scanned"
        )

        host_word = (
            "host"
            if found == 1
            else "hosts"
        )

        self.progress_hosts_var.set(
            f"{found} {host_word} discovered"
        )

    # =====================================================
    # Results
    # =====================================================
    def refresh_results(self):
        for widget in (
            self.results_container.winfo_children()
        ):
            widget.destroy()

        hosts = sorted(
            set(self.alive_hosts)
        )

        self.host_count_var.set(
            f"{len(hosts)} ONLINE"
        )

        for ip_obj in hosts:
            self.create_host_row(
                str(ip_obj)
            )

    def create_host_row(
        self,
        ip
    ):
        row = tk.Frame(
            self.results_container,
            bg=self.panel
        )

        row.pack(
            fill="x",
            pady=1
        )

        tk.Label(
            row,
            text=ip,
            width=28,
            anchor="w",
            font=("Consolas", 10),
            bg=self.panel,
            fg=self.text,
            padx=10,
            pady=7
        ).pack(
            side="left"
        )

        tk.Label(
            row,
            text="ONLINE",
            width=14,
            anchor="w",
            font=("Consolas", 9, "bold"),
            bg=self.panel,
            fg=self.accent,
            padx=5
        ).pack(
            side="left"
        )

        actions = ttk.Frame(
            row,
            style="Panel.TFrame"
        )

        actions.pack(
            side="left",
            padx=5
        )

        ttk.Button(
            actions,
            text="SSH",
            width=8,
            style="Radar.TButton",
            command=lambda host=ip: (
                self.open_putty(host)
            )
        ).pack(
            side="left",
            padx=(0, 5)
        )

        ttk.Button(
            actions,
            text="WEB",
            width=8,
            style="Radar.TButton",
            command=lambda host=ip: (
                self.open_https(host)
            )
        ).pack(
            side="left"
        )

    # =====================================================
    # PuTTY / SSH
    # =====================================================
    def open_putty(
        self,
        ip
    ):
        if (
            platform.system().lower()
            != "windows"
        ):
            messagebox.showerror(
                "SSH",
                "PuTTY integration is currently configured for Windows."
            )
            return

        putty_path = self.find_putty()

        if not putty_path:
            messagebox.showerror(
                "PuTTY Not Found",
                "RADAR could not locate putty.exe.\n\n"
                "Open HELP to check PuTTY integration."
            )
            return

        try:
            subprocess.Popen(
                [
                    putty_path,
                    "-ssh",
                    ip
                ]
            )

            self.status_var.set(
                f"SSH session launched | {ip}"
            )

        except OSError as error:
            messagebox.showerror(
                "SSH Error",
                str(error)
            )

    # =====================================================
    # HTTPS
    # =====================================================
    def open_https(
        self,
        ip
    ):
        url = f"https://{ip}"

        try:
            webbrowser.open_new_tab(
                url
            )

            self.status_var.set(
                f"Web management opened | {url}"
            )

        except Exception as error:
            messagebox.showerror(
                "Browser Error",
                str(error)
            )

    # =====================================================
    # Finish / Stop
    # =====================================================
    def scan_finished(
        self,
        elapsed
    ):
        self.scan_button.config(
            state="normal"
        )

        self.stop_button.config(
            state="disabled"
        )

        self.refresh_results()

        found = len(
            self.alive_hosts
        )

        if self.stop_event.is_set():
            self.status_var.set(
                f"Sweep stopped | "
                f"{found} hosts discovered | "
                f"{elapsed:.2f} seconds"
            )

        else:
            self.progress["value"] = (
                self.progress["maximum"]
            )

            self.percent_var.set(
                "100%"
            )

            total = int(
                self.progress["maximum"]
            )

            self.scan_count_var.set(
                f"{total:,} / {total:,} scanned"
            )

            self.status_var.set(
                f"Sweep complete | "
                f"{found} hosts discovered | "
                f"{elapsed:.2f} seconds"
            )

    def stop_scan(self):
        self.stop_event.set()

        self.stop_button.config(
            state="disabled"
        )

        self.status_var.set(
            "Stopping RADAR sweep..."
        )

    # =====================================================
    # Clear
    # =====================================================
    def clear_results(self):
        for widget in (
            self.results_container.winfo_children()
        ):
            widget.destroy()

        self.alive_hosts = []

        self.progress["value"] = 0

        self.percent_var.set(
            "0%"
        )

        self.scan_count_var.set(
            "0 / 0 scanned"
        )

        self.progress_hosts_var.set(
            "0 hosts discovered"
        )

        self.host_count_var.set(
            "0 ONLINE"
        )

        if not (
            self.scan_thread
            and self.scan_thread.is_alive()
        ):
            self.status_var.set(
                "RADAR ready."
            )

    # =====================================================
    # Copy
    # =====================================================
    def copy_results(self):
        hosts = sorted(
            set(self.alive_hosts)
        )

        if not hosts:
            messagebox.showinfo(
                "No Results",
                "No discovered hosts are available to copy."
            )
            return

        text = "\n".join(
            str(ip)
            for ip in hosts
        )

        self.root.clipboard_clear()
        self.root.clipboard_append(
            text
        )

        self.status_var.set(
            f"{len(hosts)} IP addresses copied to clipboard"
        )

    # =====================================================
    # Export
    # =====================================================
    def export_csv(self):
        hosts = sorted(
            set(self.alive_hosts)
        )

        if not hosts:
            messagebox.showinfo(
                "No Results",
                "No discovered hosts are available to export."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Export RADAR Results",
            defaultextension=".csv",
            initialfile="radar_results.csv",
            filetypes=[
                (
                    "CSV Files",
                    "*.csv"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not filename:
            return

        try:
            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerow(
                    [
                        "IP Address",
                        "Status"
                    ]
                )

                for ip in hosts:
                    writer.writerow(
                        [
                            str(ip),
                            "ONLINE"
                        ]
                    )

            self.status_var.set(
                f"RADAR results exported | {filename}"
            )

        except OSError as error:
            messagebox.showerror(
                "Export Failed",
                str(error)
            )


def main():
    root = tk.Tk()

    app = RadarApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()
