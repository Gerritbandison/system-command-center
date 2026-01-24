#!/usr/bin/env python3
"""
SYSTEM COMMAND CENTER v2
Comprehensive monitoring dashboard for Intel Arc B580 + AMD Ryzen systems
Now with GPU temperature via Intel PMT telemetry!

NOTE: Run with sudo for GPU temperature access:
    sudo python3 system_command_center_v2.py
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import struct
import re
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta


class SystemCommandCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ SYSTEM COMMAND CENTER v2")
        self.root.configure(bg="#0a0a0f")
        
        # Make fullscreen-ish
        self.root.geometry("1280x900")
        self.root.minsize(1100, 800)
        
        # Color scheme - critical/military aesthetic
        self.colors = {
            "bg_dark": "#0a0a0f",
            "bg_panel": "#0d1117",
            "bg_card": "#161b22",
            "border": "#21262d",
            "accent_red": "#ff4444",
            "accent_orange": "#ff8c00",
            "accent_yellow": "#ffd700",
            "accent_green": "#00ff88",
            "accent_blue": "#00bfff",
            "accent_purple": "#a855f7",
            "accent_cyan": "#00ffff",
            "accent_pink": "#ff6b9d",
            "text_bright": "#ffffff",
            "text_normal": "#c9d1d9",
            "text_dim": "#6e7681",
            "critical": "#ff0040",
            "warning": "#ffaa00",
            "nominal": "#00ff88",
            "grid_line": "#1a1f26"
        }
        
        # Data storage
        self.cpu_history = [0] * 60
        self.mem_history = [0] * 60
        self.gpu_temp_history = [0] * 60
        self.cpu_temp_history = [0] * 60
        self.net_rx_history = [0] * 60
        self.net_tx_history = [0] * 60
        self.last_net_rx = 0
        self.last_net_tx = 0
        self.last_net_time = time.time()
        self.start_time = datetime.now()
        
        # Check if running as root (needed for GPU temps)
        self.has_root = os.geteuid() == 0
        
        self.setup_ui()
        self.update_all()
        self.blink_cycle()
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main)
        
        # Content area
        content = tk.Frame(main, bg=self.colors["bg_dark"])
        content.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left column (40%)
        left_col = tk.Frame(content, bg=self.colors["bg_dark"], width=450)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left_col.pack_propagate(False)
        
        # Right column (60%)
        right_col = tk.Frame(content, bg=self.colors["bg_dark"])
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Left column panels
        self.create_gpu_panel(left_col)
        self.create_cpu_panel(left_col)
        self.create_memory_panel(left_col)
        
        # Right column panels
        right_top = tk.Frame(right_col, bg=self.colors["bg_dark"])
        right_top.pack(fill="x", pady=(0, 5))
        
        self.create_system_status_panel(right_top)
        self.create_storage_panel(right_col)
        self.create_network_panel(right_col)
        self.create_processes_panel(right_col)
    
    def create_header(self, parent):
        header = tk.Frame(parent, bg=self.colors["bg_panel"], height=70)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Left side - Title
        left = tk.Frame(header, bg=self.colors["bg_panel"])
        left.pack(side="left", fill="y", padx=15)
        
        title_frame = tk.Frame(left, bg=self.colors["bg_panel"])
        title_frame.pack(side="left", pady=10)
        
        title = tk.Label(
            title_frame,
            text="◆ SYSTEM COMMAND CENTER",
            font=("Monospace", 18, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_panel"]
        )
        title.pack(anchor="w")
        
        subtitle = tk.Label(
            title_frame,
            text="INTEL ARC B580 + AMD RYZEN 7 MONITORING STATION",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        subtitle.pack(anchor="w")
        
        # Status indicator
        status_frame = tk.Frame(left, bg=self.colors["bg_panel"])
        status_frame.pack(side="left", padx=(30, 0), pady=15)
        
        self.status_dot = tk.Label(
            status_frame,
            text="●",
            font=("Monospace", 14),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.status_dot.pack(side="left")
        
        self.status_text = tk.Label(
            status_frame,
            text="ALL SYSTEMS NOMINAL",
            font=("Monospace", 10, "bold"),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.status_text.pack(side="left", padx=(8, 0))
        
        # Root warning if not root
        if not self.has_root:
            warn_label = tk.Label(
                status_frame,
                text="  ⚠ Run with sudo for GPU temps",
                font=("Monospace", 9),
                fg=self.colors["warning"],
                bg=self.colors["bg_panel"]
            )
            warn_label.pack(side="left", padx=(15, 0))
        
        # Right side - Time and uptime
        right = tk.Frame(header, bg=self.colors["bg_panel"])
        right.pack(side="right", fill="y", padx=15)
        
        time_frame = tk.Frame(right, bg=self.colors["bg_panel"])
        time_frame.pack(side="right", pady=10)
        
        self.time_label = tk.Label(
            time_frame,
            text="00:00:00",
            font=("Monospace", 24, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.time_label.pack(anchor="e")
        
        self.date_label = tk.Label(
            time_frame,
            text="",
            font=("Monospace", 10),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.date_label.pack(anchor="e")
        
        # Center - hostname and kernel
        center = tk.Frame(header, bg=self.colors["bg_panel"])
        center.pack(side="right", fill="y", padx=30)
        
        hostname = subprocess.getoutput("hostname").strip()
        kernel = subprocess.getoutput("uname -r").strip()
        
        self.hostname_label = tk.Label(
            center,
            text=f"◈ {hostname.upper()}",
            font=("Monospace", 12, "bold"),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        )
        self.hostname_label.pack(pady=(15, 0))
        
        self.kernel_label = tk.Label(
            center,
            text=f"KERNEL {kernel}",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.kernel_label.pack()
    
    def create_panel(self, parent, title, height=None, expand=False):
        """Create a styled panel with title"""
        container = tk.Frame(parent, bg=self.colors["bg_dark"])
        container.pack(fill="both", expand=expand, pady=(0, 8))
        
        panel = tk.Frame(
            container, 
            bg=self.colors["bg_panel"],
            highlightbackground=self.colors["border"],
            highlightthickness=1
        )
        panel.pack(fill="both", expand=True)
        
        if height:
            panel.configure(height=height)
            panel.pack_propagate(False)
        
        # Title bar
        title_bar = tk.Frame(panel, bg=self.colors["bg_card"], height=30)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        
        tk.Label(
            title_bar,
            text=f"▸ {title}",
            font=("Monospace", 10, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_card"]
        ).pack(side="left", padx=12, pady=6)
        
        # Content area
        content = tk.Frame(panel, bg=self.colors["bg_panel"])
        content.pack(fill="both", expand=True, padx=12, pady=10)
        
        return content
    
    def create_gpu_panel(self, parent):
        """GPU monitoring panel with temps and frequency"""
        content = self.create_panel(parent, "GPU — INTEL ARC B580", height=220)
        
        # Top row - temps and frequency
        top_row = tk.Frame(content, bg=self.colors["bg_panel"])
        top_row.pack(fill="x")
        
        # GPU Temp 1 (likely hotspot/junction)
        temp1_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        temp1_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            temp1_frame,
            text="GPU TEMP",
            font=("Monospace", 9),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.gpu_temp1_label = tk.Label(
            temp1_frame,
            text="--°C",
            font=("Monospace", 32, "bold"),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_temp1_label.pack(anchor="w")
        
        self.gpu_temp1_status = tk.Label(
            temp1_frame,
            text="● STANDBY",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_temp1_status.pack(anchor="w")
        
        # GPU Temp 2 (likely edge/memory)
        temp2_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        temp2_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            temp2_frame,
            text="HOTSPOT",
            font=("Monospace", 9),
            fg=self.colors["accent_pink"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.gpu_temp2_label = tk.Label(
            temp2_frame,
            text="--°C",
            font=("Monospace", 32, "bold"),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_temp2_label.pack(anchor="w")
        
        self.gpu_temp2_status = tk.Label(
            temp2_frame,
            text="● STANDBY",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_temp2_status.pack(anchor="w")
        
        # GPU Frequency
        freq_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        freq_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(
            freq_frame,
            text="GPU CLOCK",
            font=("Monospace", 9),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="e")
        
        self.gpu_freq_label = tk.Label(
            freq_frame,
            text="-- MHz",
            font=("Monospace", 24, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_freq_label.pack(anchor="e")
        
        self.gpu_freq_max = tk.Label(
            freq_frame,
            text="MAX: -- MHz",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_freq_max.pack(anchor="e")
        
        # Temperature graph
        graph_label = tk.Label(
            content,
            text="THERMAL HISTORY (60s)",
            font=("Monospace", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        graph_label.pack(anchor="w", pady=(15, 3))
        
        self.gpu_temp_canvas = tk.Canvas(
            content,
            bg=self.colors["bg_card"],
            height=60,
            highlightthickness=0
        )
        self.gpu_temp_canvas.pack(fill="x")
    
    def create_cpu_panel(self, parent):
        """CPU monitoring panel"""
        content = self.create_panel(parent, "CPU — AMD RYZEN 7", height=200)
        
        # Top row
        top_row = tk.Frame(content, bg=self.colors["bg_panel"])
        top_row.pack(fill="x")
        
        # CPU Usage
        usage_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        usage_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            usage_frame,
            text="UTILIZATION",
            font=("Monospace", 9),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.cpu_percent_label = tk.Label(
            usage_frame,
            text="0%",
            font=("Monospace", 32, "bold"),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_percent_label.pack(anchor="w")
        
        # CPU Temp
        temp_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        temp_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            temp_frame,
            text="CPU TEMP",
            font=("Monospace", 9),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.cpu_temp_label = tk.Label(
            temp_frame,
            text="--°C",
            font=("Monospace", 32, "bold"),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_temp_label.pack(anchor="w")
        
        self.cpu_temp_status = tk.Label(
            temp_frame,
            text="● NOMINAL",
            font=("Monospace", 9),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_temp_status.pack(anchor="w")
        
        # CPU Info
        info_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        info_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(
            info_frame,
            text="FREQUENCY",
            font=("Monospace", 9),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="e")
        
        self.cpu_freq_label = tk.Label(
            info_frame,
            text="0 MHz",
            font=("Monospace", 18, "bold"),
            fg=self.colors["text_normal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_freq_label.pack(anchor="e")
        
        self.cpu_cores_label = tk.Label(
            info_frame,
            text="0 cores / 0 threads",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_cores_label.pack(anchor="e")
        
        # CPU Graph
        self.cpu_canvas = tk.Canvas(
            content,
            bg=self.colors["bg_card"],
            height=50,
            highlightthickness=0
        )
        self.cpu_canvas.pack(fill="x", pady=(15, 0))
    
    def create_memory_panel(self, parent):
        """Memory panel"""
        content = self.create_panel(parent, "MEMORY ALLOCATION", height=160)
        
        # RAM section
        ram_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        ram_frame.pack(fill="x", pady=(0, 12))
        
        ram_header = tk.Frame(ram_frame, bg=self.colors["bg_panel"])
        ram_header.pack(fill="x")
        
        tk.Label(
            ram_header,
            text="RAM",
            font=("Monospace", 11, "bold"),
            fg=self.colors["accent_purple"],
            bg=self.colors["bg_panel"]
        ).pack(side="left")
        
        self.ram_percent = tk.Label(
            ram_header,
            text="0%",
            font=("Monospace", 11, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.ram_percent.pack(side="right")
        
        # RAM bar
        self.ram_bar_frame = tk.Frame(ram_frame, bg=self.colors["bg_card"], height=22)
        self.ram_bar_frame.pack(fill="x", pady=(5, 0))
        self.ram_bar_frame.pack_propagate(False)
        
        self.ram_bar = tk.Frame(self.ram_bar_frame, bg=self.colors["accent_purple"], width=0)
        self.ram_bar.pack(side="left", fill="y")
        
        self.ram_details = tk.Label(
            ram_frame,
            text="0 GB / 0 GB",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.ram_details.pack(anchor="w", pady=(3, 0))
        
        # Swap section
        swap_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        swap_frame.pack(fill="x")
        
        swap_header = tk.Frame(swap_frame, bg=self.colors["bg_panel"])
        swap_header.pack(fill="x")
        
        tk.Label(
            swap_header,
            text="SWAP",
            font=("Monospace", 11, "bold"),
            fg=self.colors["accent_yellow"],
            bg=self.colors["bg_panel"]
        ).pack(side="left")
        
        self.swap_percent = tk.Label(
            swap_header,
            text="0%",
            font=("Monospace", 11, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.swap_percent.pack(side="right")
        
        # Swap bar
        self.swap_bar_frame = tk.Frame(swap_frame, bg=self.colors["bg_card"], height=14)
        self.swap_bar_frame.pack(fill="x", pady=(5, 0))
        self.swap_bar_frame.pack_propagate(False)
        
        self.swap_bar = tk.Frame(self.swap_bar_frame, bg=self.colors["accent_yellow"], width=0)
        self.swap_bar.pack(side="left", fill="y")
        
        self.swap_details = tk.Label(
            swap_frame,
            text="0 GB / 0 GB",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.swap_details.pack(anchor="w", pady=(3, 0))
    
    def create_system_status_panel(self, parent):
        """System status overview"""
        content = self.create_panel(parent, "SYSTEM STATUS", height=90)
        
        # Grid of status items
        grid = tk.Frame(content, bg=self.colors["bg_panel"])
        grid.pack(fill="both", expand=True)
        
        status_items = [
            ("UPTIME", "uptime", self.colors["accent_cyan"]),
            ("PROCESSES", "procs", self.colors["accent_green"]),
            ("LOAD AVG", "load", self.colors["accent_orange"]),
            ("USERS", "users", self.colors["accent_purple"]),
            ("THREADS", "threads", self.colors["accent_pink"]),
        ]
        
        self.status_values = {}
        
        for i, (label, key, color) in enumerate(status_items):
            frame = tk.Frame(grid, bg=self.colors["bg_panel"])
            frame.pack(side="left", expand=True, fill="both", padx=5)
            
            tk.Label(
                frame,
                text=label,
                font=("Monospace", 8),
                fg=self.colors["text_dim"],
                bg=self.colors["bg_panel"]
            ).pack()
            
            val_label = tk.Label(
                frame,
                text="--",
                font=("Monospace", 16, "bold"),
                fg=color,
                bg=self.colors["bg_panel"]
            )
            val_label.pack()
            self.status_values[key] = val_label
    
    def create_storage_panel(self, parent):
        """Storage panel"""
        content = self.create_panel(parent, "STORAGE DEVICES", height=130)
        
        self.storage_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.storage_frame.pack(fill="both", expand=True)
    
    def create_network_panel(self, parent):
        """Network panel"""
        content = self.create_panel(parent, "NETWORK I/O", height=130)
        
        # Stats row
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        # Download
        dl_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        dl_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            dl_frame,
            text="▼ DOWNLOAD",
            font=("Monospace", 9),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.net_dl_label = tk.Label(
            dl_frame,
            text="0 B/s",
            font=("Monospace", 18, "bold"),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        )
        self.net_dl_label.pack(anchor="w")
        
        self.net_dl_total = tk.Label(
            dl_frame,
            text="Total: 0 B",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.net_dl_total.pack(anchor="w")
        
        # Upload
        ul_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        ul_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(
            ul_frame,
            text="▲ UPLOAD",
            font=("Monospace", 9),
            fg=self.colors["accent_red"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="e")
        
        self.net_ul_label = tk.Label(
            ul_frame,
            text="0 B/s",
            font=("Monospace", 18, "bold"),
            fg=self.colors["accent_red"],
            bg=self.colors["bg_panel"]
        )
        self.net_ul_label.pack(anchor="e")
        
        self.net_ul_total = tk.Label(
            ul_frame,
            text="Total: 0 B",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.net_ul_total.pack(anchor="e")
        
        # Network graph
        self.net_canvas = tk.Canvas(
            content,
            bg=self.colors["bg_card"],
            height=40,
            highlightthickness=0
        )
        self.net_canvas.pack(fill="x", pady=(8, 0))
    
    def create_processes_panel(self, parent):
        """Top processes panel"""
        content = self.create_panel(parent, "TOP PROCESSES BY CPU", expand=True)
        
        # Header
        header = tk.Frame(content, bg=self.colors["bg_panel"])
        header.pack(fill="x")
        
        cols = [("PROCESS", 30), ("CPU%", 8), ("MEM%", 8), ("PID", 10)]
        for text, width in cols:
            tk.Label(
                header,
                text=text,
                font=("Monospace", 9, "bold"),
                fg=self.colors["text_dim"],
                bg=self.colors["bg_panel"],
                width=width,
                anchor="w"
            ).pack(side="left")
        
        # Separator
        sep = tk.Frame(content, bg=self.colors["border"], height=1)
        sep.pack(fill="x", pady=(5, 5))
        
        # Process list
        self.process_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.process_frame.pack(fill="both", expand=True)
        
        self.process_labels = []
        for i in range(8):
            row = tk.Frame(self.process_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=2)
            
            labels = []
            widths = [30, 8, 8, 10]
            for j, w in enumerate(widths):
                color = self.colors["text_normal"] if j == 0 else self.colors["text_dim"]
                lbl = tk.Label(
                    row,
                    text="--",
                    font=("Monospace", 9),
                    fg=color,
                    bg=self.colors["bg_panel"],
                    width=w,
                    anchor="w"
                )
                lbl.pack(side="left")
                labels.append(lbl)
            self.process_labels.append(labels)
    
    # ==================== DATA FETCHING ====================
    
    def get_gpu_temps(self):
        """Get Intel Arc GPU temperatures from PMT telemetry"""
        if not self.has_root:
            return None, None
        
        try:
            with open('/sys/class/intel_pmt/telem2/telem', 'rb') as f:
                data = f.read()
                # Offset 0xa4: GPU temp sensor 1
                # Offset 0xa8: GPU temp sensor 2 (hotspot)
                temp1 = struct.unpack('<I', data[0xa4:0xa8])[0]
                temp2 = struct.unpack('<I', data[0xa8:0xac])[0]
                
                # Sanity check - temps should be reasonable
                if 0 < temp1 < 120 and 0 < temp2 < 120:
                    return temp1, temp2
            return None, None
        except:
            return None, None
    
    def get_gpu_frequency(self):
        """Get GPU frequency from sysfs"""
        try:
            cur_freq = Path("/sys/class/drm/card1/device/tile0/gt0/freq0/act_freq").read_text().strip()
            max_freq = Path("/sys/class/drm/card1/device/tile0/gt0/freq0/max_freq").read_text().strip()
            return int(cur_freq), int(max_freq)
        except:
            return None, None
    
    def get_cpu_temp(self):
        """Get AMD Ryzen CPU temperature from hwmon (k10temp)"""
        try:
            temp_file = Path("/sys/class/hwmon/hwmon2/temp1_input")
            if temp_file.exists():
                return int(temp_file.read_text().strip()) / 1000
            return None
        except:
            return None
    
    def get_cpu_usage(self):
        try:
            output = subprocess.getoutput("grep 'cpu ' /proc/stat")
            parts = output.split()
            idle = int(parts[4])
            total = sum(int(p) for p in parts[1:])
            
            if hasattr(self, 'last_cpu_idle'):
                diff_idle = idle - self.last_cpu_idle
                diff_total = total - self.last_cpu_total
                usage = 100 * (1 - diff_idle / diff_total) if diff_total > 0 else 0
            else:
                usage = 0
            
            self.last_cpu_idle = idle
            self.last_cpu_total = total
            return max(0, min(100, usage))
        except:
            return 0
    
    def get_cpu_freq(self):
        try:
            freqs = []
            output = subprocess.getoutput("grep 'MHz' /proc/cpuinfo")
            for line in output.split('\n'):
                match = re.search(r':\s*(\d+)', line)
                if match:
                    freqs.append(int(float(match.group(1))))
            return int(sum(freqs) / len(freqs)) if freqs else 0
        except:
            return 0
    
    def get_cpu_info(self):
        try:
            cores = int(subprocess.getoutput("grep -c 'processor' /proc/cpuinfo"))
            physical = subprocess.getoutput("grep 'cpu cores' /proc/cpuinfo | head -1")
            match = re.search(r'(\d+)', physical)
            phys_cores = int(match.group(1)) if match else cores // 2
            return phys_cores, cores
        except:
            return 0, 0
    
    def get_memory_info(self):
        try:
            output = subprocess.getoutput("free -b")
            lines = output.split('\n')
            
            mem_parts = lines[1].split()
            mem_total = int(mem_parts[1])
            mem_used = int(mem_parts[2])
            
            swap_parts = lines[2].split()
            swap_total = int(swap_parts[1])
            swap_used = int(swap_parts[2])
            
            return {
                'mem_total': mem_total,
                'mem_used': mem_used,
                'mem_percent': (mem_used / mem_total * 100) if mem_total > 0 else 0,
                'swap_total': swap_total,
                'swap_used': swap_used,
                'swap_percent': (swap_used / swap_total * 100) if swap_total > 0 else 0
            }
        except:
            return None
    
    def get_storage_info(self):
        try:
            output = subprocess.getoutput("df -B1 -x tmpfs -x devtmpfs -x squashfs -x overlay 2>/dev/null | tail -n +2")
            disks = []
            seen_mounts = set()
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 6 and parts[5] not in seen_mounts:
                        seen_mounts.add(parts[5])
                        disks.append({
                            'device': parts[0].split('/')[-1],
                            'total': int(parts[1]),
                            'used': int(parts[2]),
                            'mount': parts[5],
                            'percent': int(parts[4].replace('%', ''))
                        })
            return disks
        except:
            return []
    
    def get_network_speed(self):
        try:
            rx_total = 0
            tx_total = 0
            
            net_path = Path("/sys/class/net")
            for iface in net_path.iterdir():
                if iface.name not in ('lo', 'docker0') and not iface.name.startswith('veth'):
                    rx_file = iface / "statistics/rx_bytes"
                    tx_file = iface / "statistics/tx_bytes"
                    if rx_file.exists():
                        rx_total += int(rx_file.read_text().strip())
                    if tx_file.exists():
                        tx_total += int(tx_file.read_text().strip())
            
            now = time.time()
            elapsed = now - self.last_net_time
            
            rx_speed = (rx_total - self.last_net_rx) / elapsed if elapsed > 0 and self.last_net_rx > 0 else 0
            tx_speed = (tx_total - self.last_net_tx) / elapsed if elapsed > 0 and self.last_net_tx > 0 else 0
            
            self.last_net_rx = rx_total
            self.last_net_tx = tx_total
            self.last_net_time = now
            
            return max(0, rx_speed), max(0, tx_speed), rx_total, tx_total
        except:
            return 0, 0, 0, 0
    
    def get_top_processes(self):
        try:
            output = subprocess.getoutput("ps aux --sort=-%cpu | head -9 | tail -8")
            procs = []
            for line in output.strip().split('\n'):
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    name = parts[10].split()[0].split('/')[-1][:28]
                    procs.append({
                        'name': name,
                        'cpu': parts[2],
                        'mem': parts[3],
                        'pid': parts[1]
                    })
            return procs
        except:
            return []
    
    def get_system_stats(self):
        try:
            # Uptime
            uptime_sec = float(Path("/proc/uptime").read_text().split()[0])
            days = int(uptime_sec // 86400)
            hours = int((uptime_sec % 86400) // 3600)
            mins = int((uptime_sec % 3600) // 60)
            if days > 0:
                uptime_str = f"{days}d {hours}h"
            else:
                uptime_str = f"{hours}h {mins}m"
            
            # Process and thread count
            procs = 0
            threads = 0
            for p in Path("/proc").iterdir():
                if p.name.isdigit():
                    procs += 1
                    try:
                        threads += len(list((p / "task").iterdir()))
                    except:
                        pass
            
            # Load average
            load = Path("/proc/loadavg").read_text().split()[0]
            
            # Users
            users = subprocess.getoutput("who | wc -l").strip()
            
            return {
                'uptime': uptime_str,
                'procs': str(procs),
                'threads': str(threads),
                'load': load,
                'users': users
            }
        except:
            return {'uptime': '--', 'procs': '--', 'threads': '--', 'load': '--', 'users': '--'}
    
    def format_bytes(self, b):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if b < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024
        return f"{b:.1f} PB"
    
    def format_speed(self, bps):
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if bps < 1024:
                return f"{bps:.1f} {unit}"
            bps /= 1024
        return f"{bps:.1f} TB/s"
    
    def get_temp_color_status(self, temp, thresholds=(55, 75)):
        """Get color and status based on temperature"""
        if temp is None:
            return self.colors["text_dim"], "● OFFLINE"
        
        low, high = thresholds
        if temp < low:
            return self.colors["nominal"], "● NOMINAL"
        elif temp < high:
            return self.colors["warning"], "● ELEVATED"
        else:
            return self.colors["critical"], "● CRITICAL"
    
    # ==================== DRAWING ====================
    
    def draw_graph(self, canvas, data, color, max_val=100):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w <= 1:
            return
        
        # Draw grid lines
        for i in range(1, 4):
            y = h * i / 4
            canvas.create_line(0, y, w, y, fill=self.colors["grid_line"], dash=(2, 4))
        
        # Draw data
        if len(data) > 1 and max_val > 0:
            points = []
            for i, val in enumerate(data):
                x = w * i / (len(data) - 1)
                y = h - (h * min(val, max_val) / max_val)
                points.append((x, y))
            
            # Fill area
            fill_points = [(0, h)] + points + [(w, h)]
            canvas.create_polygon(fill_points, fill=color, stipple="gray25", outline="")
            
            # Line
            for i in range(len(points) - 1):
                canvas.create_line(
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    fill=color, width=2
                )
    
    def draw_dual_graph(self, canvas, data1, color1, data2, color2, max_val=100):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w <= 1:
            return
        
        # Draw grid
        for i in range(1, 4):
            y = h * i / 4
            canvas.create_line(0, y, w, y, fill=self.colors["grid_line"], dash=(2, 4))
        
        # Draw both lines
        for data, color in [(data1, color1), (data2, color2)]:
            if len(data) > 1 and max_val > 0:
                points = []
                for i, val in enumerate(data):
                    x = w * i / (len(data) - 1)
                    y = h - (h * min(val, max_val) / max_val)
                    points.append((x, y))
                
                for i in range(len(points) - 1):
                    canvas.create_line(
                        points[i][0], points[i][1],
                        points[i+1][0], points[i+1][1],
                        fill=color, width=2
                    )
    
    # ==================== UI UPDATES ====================
    
    def update_gpu(self):
        # Temperatures
        temp1, temp2 = self.get_gpu_temps()
        
        if temp1 is not None:
            self.gpu_temp1_label.config(text=f"{temp1}°C")
            color, status = self.get_temp_color_status(temp1, (55, 80))
            self.gpu_temp1_label.config(fg=color)
            self.gpu_temp1_status.config(text=status, fg=color)
            
            self.gpu_temp_history.pop(0)
            self.gpu_temp_history.append(temp1)
        else:
            self.gpu_temp1_label.config(text="--°C", fg=self.colors["text_dim"])
            self.gpu_temp1_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
        if temp2 is not None:
            self.gpu_temp2_label.config(text=f"{temp2}°C")
            color, status = self.get_temp_color_status(temp2, (60, 85))
            self.gpu_temp2_label.config(fg=color)
            self.gpu_temp2_status.config(text=status, fg=color)
        else:
            self.gpu_temp2_label.config(text="--°C", fg=self.colors["text_dim"])
            self.gpu_temp2_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
        # Frequency
        cur_freq, max_freq = self.get_gpu_frequency()
        if cur_freq is not None:
            self.gpu_freq_label.config(text=f"{cur_freq} MHz")
            self.gpu_freq_max.config(text=f"MAX: {max_freq} MHz")
        
        # Draw temp graph
        self.draw_graph(self.gpu_temp_canvas, self.gpu_temp_history, self.colors["accent_blue"], max_val=100)
    
    def update_cpu(self):
        usage = self.get_cpu_usage()
        temp = self.get_cpu_temp()
        freq = self.get_cpu_freq()
        cores, threads = self.get_cpu_info()
        
        # Update history
        self.cpu_history.pop(0)
        self.cpu_history.append(usage)
        
        if temp:
            self.cpu_temp_history.pop(0)
            self.cpu_temp_history.append(temp)
        
        # Usage color
        if usage < 50:
            usage_color = self.colors["accent_green"]
        elif usage < 80:
            usage_color = self.colors["warning"]
        else:
            usage_color = self.colors["critical"]
        
        self.cpu_percent_label.config(text=f"{usage:.0f}%", fg=usage_color)
        
        # Temp
        if temp is not None:
            self.cpu_temp_label.config(text=f"{temp:.0f}°C")
            color, status = self.get_temp_color_status(temp, (55, 75))
            self.cpu_temp_label.config(fg=color)
            self.cpu_temp_status.config(text=status, fg=color)
        
        # Info
        self.cpu_freq_label.config(text=f"{freq} MHz")
        self.cpu_cores_label.config(text=f"{cores} cores / {threads} threads")
        
        # Draw graph
        self.draw_graph(self.cpu_canvas, self.cpu_history, usage_color)
    
    def update_memory(self):
        mem = self.get_memory_info()
        if mem:
            # RAM
            self.ram_percent.config(text=f"{mem['mem_percent']:.1f}%")
            self.ram_details.config(
                text=f"{self.format_bytes(mem['mem_used'])} / {self.format_bytes(mem['mem_total'])}"
            )
            
            bar_width = int(self.ram_bar_frame.winfo_width() * mem['mem_percent'] / 100)
            self.ram_bar.config(width=max(0, bar_width))
            
            # Swap
            self.swap_percent.config(text=f"{mem['swap_percent']:.1f}%")
            self.swap_details.config(
                text=f"{self.format_bytes(mem['swap_used'])} / {self.format_bytes(mem['swap_total'])}"
            )
            
            swap_width = int(self.swap_bar_frame.winfo_width() * mem['swap_percent'] / 100)
            self.swap_bar.config(width=max(0, swap_width))
    
    def update_storage(self):
        disks = self.get_storage_info()
        
        for widget in self.storage_frame.winfo_children():
            widget.destroy()
        
        for disk in disks[:4]:
            row = tk.Frame(self.storage_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=3)
            
            # Name
            mount_text = disk['mount'] if len(disk['mount']) <= 20 else disk['mount'][:17] + "..."
            tk.Label(
                row,
                text=f"{mount_text}",
                font=("Monospace", 9),
                fg=self.colors["text_normal"],
                bg=self.colors["bg_panel"],
                width=22,
                anchor="w"
            ).pack(side="left")
            
            # Percent
            percent = disk['percent']
            if percent < 70:
                color = self.colors["accent_green"]
            elif percent < 90:
                color = self.colors["warning"]
            else:
                color = self.colors["critical"]
            
            tk.Label(
                row,
                text=f"{percent}%",
                font=("Monospace", 10, "bold"),
                fg=color,
                bg=self.colors["bg_panel"],
                width=5
            ).pack(side="right")
            
            # Size info
            tk.Label(
                row,
                text=f"{self.format_bytes(disk['used'])} / {self.format_bytes(disk['total'])}",
                font=("Monospace", 9),
                fg=self.colors["text_dim"],
                bg=self.colors["bg_panel"]
            ).pack(side="right", padx=(0, 10))
            
            # Bar
            bar_frame = tk.Frame(row, bg=self.colors["bg_card"], height=12, width=80)
            bar_frame.pack(side="right", padx=5)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg=color, width=int(80 * percent / 100))
            bar.pack(side="left", fill="y")
    
    def update_network(self):
        rx, tx, rx_total, tx_total = self.get_network_speed()
        
        self.net_dl_label.config(text=self.format_speed(rx))
        self.net_ul_label.config(text=self.format_speed(tx))
        self.net_dl_total.config(text=f"Total: {self.format_bytes(rx_total)}")
        self.net_ul_total.config(text=f"Total: {self.format_bytes(tx_total)}")
        
        self.net_rx_history.pop(0)
        self.net_rx_history.append(rx)
        self.net_tx_history.pop(0)
        self.net_tx_history.append(tx)
        
        max_net = max(max(self.net_rx_history), max(self.net_tx_history), 1024)
        self.draw_dual_graph(
            self.net_canvas,
            self.net_rx_history, self.colors["accent_green"],
            self.net_tx_history, self.colors["accent_red"],
            max_val=max_net
        )
    
    def update_processes(self):
        procs = self.get_top_processes()
        
        for i, labels in enumerate(self.process_labels):
            if i < len(procs):
                p = procs[i]
                labels[0].config(text=p['name'], fg=self.colors["text_normal"])
                
                # Color CPU usage
                try:
                    cpu_val = float(p['cpu'])
                    if cpu_val > 50:
                        cpu_color = self.colors["critical"]
                    elif cpu_val > 20:
                        cpu_color = self.colors["warning"]
                    else:
                        cpu_color = self.colors["text_dim"]
                except:
                    cpu_color = self.colors["text_dim"]
                
                labels[1].config(text=p['cpu'], fg=cpu_color)
                labels[2].config(text=p['mem'])
                labels[3].config(text=p['pid'])
            else:
                for lbl in labels:
                    lbl.config(text="--", fg=self.colors["text_dim"])
    
    def update_system_status(self):
        stats = self.get_system_stats()
        for key, val in stats.items():
            if key in self.status_values:
                self.status_values[key].config(text=val)
    
    def update_time(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A, %B %d, %Y"))
    
    def blink_cycle(self):
        current = self.status_dot.cget("fg")
        new_color = self.colors["bg_panel"] if current == self.colors["nominal"] else self.colors["nominal"]
        self.status_dot.config(fg=new_color)
        self.root.after(800, self.blink_cycle)
    
    def update_all(self):
        try:
            self.update_time()
            self.update_gpu()
            self.update_cpu()
            self.update_memory()
            self.update_storage()
            self.update_network()
            self.update_processes()
            self.update_system_status()
        except Exception as e:
            print(f"Update error: {e}")
        
        self.root.after(1000, self.update_all)


def main():
    # Check for root
    if os.geteuid() != 0:
        print("=" * 60)
        print("  NOTE: Run with sudo for GPU temperature monitoring")
        print("  sudo python3 system_command_center_v2.py")
        print("=" * 60)
        print()
    
    root = tk.Tk()
    app = SystemCommandCenter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
