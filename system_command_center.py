#!/usr/bin/env python3
"""
SYSTEM COMMAND CENTER
Comprehensive monitoring dashboard for Intel Arc B580 + AMD Ryzen systems
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta


class SystemCommandCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ SYSTEM COMMAND CENTER")
        self.root.configure(bg="#0a0a0f")
        
        # Make fullscreen-ish
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
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
        self.net_rx_history = [0] * 60
        self.net_tx_history = [0] * 60
        self.last_net_rx = 0
        self.last_net_tx = 0
        self.last_net_time = time.time()
        self.start_time = datetime.now()
        
        self.setup_ui()
        self.update_all()
    
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
        left_col = tk.Frame(content, bg=self.colors["bg_dark"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Right column (60%)
        right_col = tk.Frame(content, bg=self.colors["bg_dark"])
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Left column panels
        self.create_thermal_panel(left_col)
        self.create_cpu_panel(left_col)
        self.create_memory_panel(left_col)
        
        # Right column panels
        self.create_system_status_panel(right_col)
        self.create_storage_panel(right_col)
        self.create_network_panel(right_col)
        self.create_processes_panel(right_col)
    
    def create_header(self, parent):
        header = tk.Frame(parent, bg=self.colors["bg_panel"], height=60)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Left side - Title
        left = tk.Frame(header, bg=self.colors["bg_panel"])
        left.pack(side="left", fill="y", padx=15)
        
        title = tk.Label(
            left,
            text="◆ SYSTEM COMMAND CENTER",
            font=("Monospace", 16, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_panel"]
        )
        title.pack(side="left", pady=15)
        
        # Blinking status indicator
        self.status_dot = tk.Label(
            left,
            text="●",
            font=("Monospace", 12),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.status_dot.pack(side="left", padx=(10, 0))
        
        status_text = tk.Label(
            left,
            text="SYSTEMS NOMINAL",
            font=("Monospace", 10),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        status_text.pack(side="left", padx=(5, 0))
        self.status_text = status_text
        
        # Right side - Time and uptime
        right = tk.Frame(header, bg=self.colors["bg_panel"])
        right.pack(side="right", fill="y", padx=15)
        
        self.time_label = tk.Label(
            right,
            text="00:00:00",
            font=("Monospace", 20, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.time_label.pack(side="right", pady=10)
        
        time_prefix = tk.Label(
            right,
            text="LOCAL TIME ",
            font=("Monospace", 10),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        time_prefix.pack(side="right", pady=15)
        
        # Center - hostname and kernel
        center = tk.Frame(header, bg=self.colors["bg_panel"])
        center.pack(side="right", fill="y", padx=30)
        
        hostname = subprocess.getoutput("hostname").strip()
        kernel = subprocess.getoutput("uname -r").strip()
        
        self.hostname_label = tk.Label(
            center,
            text=f"◈ {hostname.upper()}",
            font=("Monospace", 11, "bold"),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        )
        self.hostname_label.pack(pady=(12, 0))
        
        self.kernel_label = tk.Label(
            center,
            text=f"KERNEL {kernel}",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.kernel_label.pack()
    
    def create_panel(self, parent, title, height=None):
        """Create a styled panel with title"""
        container = tk.Frame(parent, bg=self.colors["bg_dark"])
        container.pack(fill="both", expand=(height is None), pady=(0, 8))
        
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
        title_bar = tk.Frame(panel, bg=self.colors["bg_card"], height=28)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        
        tk.Label(
            title_bar,
            text=f"▸ {title}",
            font=("Monospace", 9, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_card"]
        ).pack(side="left", padx=10, pady=5)
        
        # Content area
        content = tk.Frame(panel, bg=self.colors["bg_panel"])
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        return content
    
    def create_thermal_panel(self, parent):
        """Thermal monitoring panel"""
        content = self.create_panel(parent, "THERMAL STATUS", height=160)
        
        # Two columns for GPU and CPU
        cols = tk.Frame(content, bg=self.colors["bg_panel"])
        cols.pack(fill="both", expand=True)
        
        # GPU Thermal
        gpu_frame = tk.Frame(cols, bg=self.colors["bg_panel"])
        gpu_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(
            gpu_frame,
            text="GPU",
            font=("Monospace", 9),
            fg=self.colors["accent_blue"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        tk.Label(
            gpu_frame,
            text="INTEL ARC B580",
            font=("Monospace", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.gpu_temp_label = tk.Label(
            gpu_frame,
            text="--°C",
            font=("Monospace", 32, "bold"),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_temp_label.pack(anchor="w", pady=(5, 0))
        
        self.gpu_status = tk.Label(
            gpu_frame,
            text="● NO SENSOR",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.gpu_status.pack(anchor="w")
        
        # CPU Thermal
        cpu_frame = tk.Frame(cols, bg=self.colors["bg_panel"])
        cpu_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        tk.Label(
            cpu_frame,
            text="CPU",
            font=("Monospace", 9),
            fg=self.colors["accent_orange"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        tk.Label(
            cpu_frame,
            text="AMD RYZEN 7",
            font=("Monospace", 8),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.cpu_temp_label = tk.Label(
            cpu_frame,
            text="--°C",
            font=("Monospace", 32, "bold"),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_temp_label.pack(anchor="w", pady=(5, 0))
        
        self.cpu_temp_status = tk.Label(
            cpu_frame,
            text="● NOMINAL",
            font=("Monospace", 9),
            fg=self.colors["nominal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_temp_status.pack(anchor="w")
    
    def create_cpu_panel(self, parent):
        """CPU usage panel with graph"""
        content = self.create_panel(parent, "CPU UTILIZATION", height=180)
        
        # Top stats row
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        self.cpu_percent_label = tk.Label(
            stats,
            text="0%",
            font=("Monospace", 28, "bold"),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_percent_label.pack(side="left")
        
        cpu_info = tk.Frame(stats, bg=self.colors["bg_panel"])
        cpu_info.pack(side="right")
        
        self.cpu_freq_label = tk.Label(
            cpu_info,
            text="0 MHz",
            font=("Monospace", 10),
            fg=self.colors["text_normal"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_freq_label.pack(anchor="e")
        
        self.cpu_cores_label = tk.Label(
            cpu_info,
            text="0 cores",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        self.cpu_cores_label.pack(anchor="e")
        
        # Graph canvas
        self.cpu_canvas = tk.Canvas(
            content,
            bg=self.colors["bg_card"],
            height=80,
            highlightthickness=0
        )
        self.cpu_canvas.pack(fill="x", pady=(10, 0))
    
    def create_memory_panel(self, parent):
        """Memory panel"""
        content = self.create_panel(parent, "MEMORY ALLOCATION", height=180)
        
        # RAM section
        ram_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        ram_frame.pack(fill="x", pady=(0, 10))
        
        ram_header = tk.Frame(ram_frame, bg=self.colors["bg_panel"])
        ram_header.pack(fill="x")
        
        tk.Label(
            ram_header,
            text="RAM",
            font=("Monospace", 10, "bold"),
            fg=self.colors["accent_purple"],
            bg=self.colors["bg_panel"]
        ).pack(side="left")
        
        self.ram_percent = tk.Label(
            ram_header,
            text="0%",
            font=("Monospace", 10, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.ram_percent.pack(side="right")
        
        # RAM bar
        self.ram_bar_frame = tk.Frame(ram_frame, bg=self.colors["bg_card"], height=20)
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
            font=("Monospace", 10, "bold"),
            fg=self.colors["accent_yellow"],
            bg=self.colors["bg_panel"]
        ).pack(side="left")
        
        self.swap_percent = tk.Label(
            swap_header,
            text="0%",
            font=("Monospace", 10, "bold"),
            fg=self.colors["text_bright"],
            bg=self.colors["bg_panel"]
        )
        self.swap_percent.pack(side="right")
        
        # Swap bar
        self.swap_bar_frame = tk.Frame(swap_frame, bg=self.colors["bg_card"], height=12)
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
        content = self.create_panel(parent, "SYSTEM STATUS", height=100)
        
        # Grid of status items
        grid = tk.Frame(content, bg=self.colors["bg_panel"])
        grid.pack(fill="both", expand=True)
        
        # Configure grid columns
        for i in range(4):
            grid.columnconfigure(i, weight=1)
        
        status_items = [
            ("UPTIME", "uptime", self.colors["accent_cyan"]),
            ("PROCESSES", "procs", self.colors["accent_green"]),
            ("LOAD AVG", "load", self.colors["accent_orange"]),
            ("USERS", "users", self.colors["accent_purple"]),
        ]
        
        self.status_values = {}
        
        for i, (label, key, color) in enumerate(status_items):
            frame = tk.Frame(grid, bg=self.colors["bg_panel"])
            frame.grid(row=0, column=i, sticky="nsew", padx=5)
            
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
                font=("Monospace", 14, "bold"),
                fg=color,
                bg=self.colors["bg_panel"]
            )
            val_label.pack()
            self.status_values[key] = val_label
    
    def create_storage_panel(self, parent):
        """Storage panel"""
        content = self.create_panel(parent, "STORAGE DEVICES", height=150)
        
        self.storage_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.storage_frame.pack(fill="both", expand=True)
    
    def create_network_panel(self, parent):
        """Network panel"""
        content = self.create_panel(parent, "NETWORK I/O", height=140)
        
        # Stats row
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        # Download
        dl_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        dl_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(
            dl_frame,
            text="▼ DOWNLOAD",
            font=("Monospace", 8),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="w")
        
        self.net_dl_label = tk.Label(
            dl_frame,
            text="0 B/s",
            font=("Monospace", 16, "bold"),
            fg=self.colors["accent_green"],
            bg=self.colors["bg_panel"]
        )
        self.net_dl_label.pack(anchor="w")
        
        # Upload
        ul_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        ul_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(
            ul_frame,
            text="▲ UPLOAD",
            font=("Monospace", 8),
            fg=self.colors["accent_red"],
            bg=self.colors["bg_panel"]
        ).pack(anchor="e")
        
        self.net_ul_label = tk.Label(
            ul_frame,
            text="0 B/s",
            font=("Monospace", 16, "bold"),
            fg=self.colors["accent_red"],
            bg=self.colors["bg_panel"]
        )
        self.net_ul_label.pack(anchor="e")
        
        # Network graph
        self.net_canvas = tk.Canvas(
            content,
            bg=self.colors["bg_card"],
            height=50,
            highlightthickness=0
        )
        self.net_canvas.pack(fill="x", pady=(10, 0))
    
    def create_processes_panel(self, parent):
        """Top processes panel"""
        content = self.create_panel(parent, "TOP PROCESSES", height=200)
        
        # Header
        header = tk.Frame(content, bg=self.colors["bg_panel"])
        header.pack(fill="x")
        
        cols = [("PROCESS", 200), ("CPU%", 70), ("MEM%", 70), ("PID", 70)]
        for text, width in cols:
            tk.Label(
                header,
                text=text,
                font=("Monospace", 8),
                fg=self.colors["text_dim"],
                bg=self.colors["bg_panel"],
                width=width//8,
                anchor="w"
            ).pack(side="left")
        
        # Process list
        self.process_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.process_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        self.process_labels = []
        for i in range(6):
            row = tk.Frame(self.process_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=1)
            
            labels = []
            widths = [200, 70, 70, 70]
            for w in widths:
                lbl = tk.Label(
                    row,
                    text="--",
                    font=("Monospace", 9),
                    fg=self.colors["text_normal"],
                    bg=self.colors["bg_panel"],
                    width=w//8,
                    anchor="w"
                )
                lbl.pack(side="left")
                labels.append(lbl)
            self.process_labels.append(labels)
    
    # ==================== DATA FETCHING ====================
    
    def get_cpu_temp(self):
        try:
            temp_file = Path("/sys/class/hwmon/hwmon2/temp1_input")
            if temp_file.exists():
                return int(temp_file.read_text().strip()) / 1000
            return None
        except:
            return None
    
    def get_gpu_temp(self):
        try:
            temp_file = Path("/sys/class/hwmon/hwmon3/temp1_input")
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
            output = subprocess.getoutput("grep 'MHz' /proc/cpuinfo | head -1")
            match = re.search(r'(\d+)', output)
            return int(float(match.group(1))) if match else 0
        except:
            return 0
    
    def get_cpu_cores(self):
        try:
            return int(subprocess.getoutput("nproc"))
        except:
            return 0
    
    def get_memory_info(self):
        try:
            output = subprocess.getoutput("free -b")
            lines = output.split('\n')
            
            # RAM
            mem_parts = lines[1].split()
            mem_total = int(mem_parts[1])
            mem_used = int(mem_parts[2])
            
            # Swap
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
            output = subprocess.getoutput("df -B1 -x tmpfs -x devtmpfs -x squashfs 2>/dev/null | tail -n +2")
            disks = []
            for line in output.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
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
                if iface.name != 'lo':
                    rx_file = iface / "statistics/rx_bytes"
                    tx_file = iface / "statistics/tx_bytes"
                    if rx_file.exists():
                        rx_total += int(rx_file.read_text().strip())
                    if tx_file.exists():
                        tx_total += int(tx_file.read_text().strip())
            
            now = time.time()
            elapsed = now - self.last_net_time
            
            rx_speed = (rx_total - self.last_net_rx) / elapsed if elapsed > 0 else 0
            tx_speed = (tx_total - self.last_net_tx) / elapsed if elapsed > 0 else 0
            
            self.last_net_rx = rx_total
            self.last_net_tx = tx_total
            self.last_net_time = now
            
            return max(0, rx_speed), max(0, tx_speed)
        except:
            return 0, 0
    
    def get_top_processes(self):
        try:
            output = subprocess.getoutput("ps aux --sort=-%cpu | head -7 | tail -6")
            procs = []
            for line in output.strip().split('\n'):
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    procs.append({
                        'name': parts[10][:25],
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
            hours = int(uptime_sec // 3600)
            mins = int((uptime_sec % 3600) // 60)
            uptime_str = f"{hours}h {mins}m"
            
            # Process count
            procs = len([p for p in Path("/proc").iterdir() if p.name.isdigit()])
            
            # Load average
            load = Path("/proc/loadavg").read_text().split()[0]
            
            # Users
            users = subprocess.getoutput("who | wc -l").strip()
            
            return {
                'uptime': uptime_str,
                'procs': str(procs),
                'load': load,
                'users': users
            }
        except:
            return {'uptime': '--', 'procs': '--', 'load': '--', 'users': '--'}
    
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
    
    # ==================== UI UPDATES ====================
    
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
    
    def update_thermal(self):
        # CPU temp
        cpu_temp = self.get_cpu_temp()
        if cpu_temp is not None:
            self.cpu_temp_label.config(text=f"{cpu_temp:.0f}°C")
            if cpu_temp < 55:
                color = self.colors["nominal"]
                status = "● NOMINAL"
            elif cpu_temp < 75:
                color = self.colors["warning"]
                status = "● ELEVATED"
            else:
                color = self.colors["critical"]
                status = "● CRITICAL"
            self.cpu_temp_label.config(fg=color)
            self.cpu_temp_status.config(text=status, fg=color)
        
        # GPU temp
        gpu_temp = self.get_gpu_temp()
        if gpu_temp is not None:
            self.gpu_temp_label.config(text=f"{gpu_temp:.0f}°C", fg=self.colors["nominal"])
            self.gpu_status.config(text="● NOMINAL", fg=self.colors["nominal"])
        else:
            self.gpu_temp_label.config(text="--°C", fg=self.colors["text_dim"])
            self.gpu_status.config(text="● NO SENSOR", fg=self.colors["text_dim"])
    
    def update_cpu(self):
        usage = self.get_cpu_usage()
        freq = self.get_cpu_freq()
        cores = self.get_cpu_cores()
        
        # Update history
        self.cpu_history.pop(0)
        self.cpu_history.append(usage)
        
        # Color based on usage
        if usage < 50:
            color = self.colors["accent_green"]
        elif usage < 80:
            color = self.colors["warning"]
        else:
            color = self.colors["critical"]
        
        self.cpu_percent_label.config(text=f"{usage:.0f}%", fg=color)
        self.cpu_freq_label.config(text=f"{freq} MHz")
        self.cpu_cores_label.config(text=f"{cores} cores")
        
        # Draw graph
        self.draw_graph(self.cpu_canvas, self.cpu_history, color)
    
    def update_memory(self):
        mem = self.get_memory_info()
        if mem:
            # RAM
            self.ram_percent.config(text=f"{mem['mem_percent']:.1f}%")
            self.ram_details.config(
                text=f"{self.format_bytes(mem['mem_used'])} / {self.format_bytes(mem['mem_total'])}"
            )
            
            # RAM bar
            bar_width = int(self.ram_bar_frame.winfo_width() * mem['mem_percent'] / 100)
            self.ram_bar.config(width=max(0, bar_width))
            
            # Swap
            self.swap_percent.config(text=f"{mem['swap_percent']:.1f}%")
            self.swap_details.config(
                text=f"{self.format_bytes(mem['swap_used'])} / {self.format_bytes(mem['swap_total'])}"
            )
            
            # Swap bar
            swap_width = int(self.swap_bar_frame.winfo_width() * mem['swap_percent'] / 100)
            self.swap_bar.config(width=max(0, swap_width))
    
    def update_storage(self):
        disks = self.get_storage_info()
        
        # Clear old
        for widget in self.storage_frame.winfo_children():
            widget.destroy()
        
        for disk in disks[:4]:  # Show max 4 disks
            row = tk.Frame(self.storage_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=2)
            
            # Name and mount
            tk.Label(
                row,
                text=f"{disk['device']} ({disk['mount']})",
                font=("Monospace", 9),
                fg=self.colors["text_normal"],
                bg=self.colors["bg_panel"],
                width=25,
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
                font=("Monospace", 9, "bold"),
                fg=color,
                bg=self.colors["bg_panel"],
                width=6
            ).pack(side="right")
            
            # Bar
            bar_frame = tk.Frame(row, bg=self.colors["bg_card"], height=10, width=100)
            bar_frame.pack(side="right", padx=5)
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg=color, width=percent)
            bar.pack(side="left", fill="y")
    
    def update_network(self):
        rx, tx = self.get_network_speed()
        
        self.net_dl_label.config(text=self.format_speed(rx))
        self.net_ul_label.config(text=self.format_speed(tx))
        
        # Update history
        self.net_rx_history.pop(0)
        self.net_rx_history.append(rx)
        self.net_tx_history.pop(0)
        self.net_tx_history.append(tx)
        
        # Draw graph
        max_net = max(max(self.net_rx_history), max(self.net_tx_history), 1024)
        self.net_canvas.delete("all")
        
        w = self.net_canvas.winfo_width()
        h = self.net_canvas.winfo_height()
        
        if w > 1 and len(self.net_rx_history) > 1:
            # RX (green)
            points = []
            for i, val in enumerate(self.net_rx_history):
                x = w * i / (len(self.net_rx_history) - 1)
                y = h - (h * min(val, max_net) / max_net)
                points.append((x, y))
            
            for i in range(len(points) - 1):
                self.net_canvas.create_line(
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    fill=self.colors["accent_green"], width=2
                )
            
            # TX (red)
            points = []
            for i, val in enumerate(self.net_tx_history):
                x = w * i / (len(self.net_tx_history) - 1)
                y = h - (h * min(val, max_net) / max_net)
                points.append((x, y))
            
            for i in range(len(points) - 1):
                self.net_canvas.create_line(
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    fill=self.colors["accent_red"], width=2
                )
    
    def update_processes(self):
        procs = self.get_top_processes()
        
        for i, labels in enumerate(self.process_labels):
            if i < len(procs):
                p = procs[i]
                labels[0].config(text=p['name'])
                labels[1].config(text=p['cpu'])
                labels[2].config(text=p['mem'])
                labels[3].config(text=p['pid'])
            else:
                for lbl in labels:
                    lbl.config(text="--")
    
    def update_system_status(self):
        stats = self.get_system_stats()
        for key, val in stats.items():
            if key in self.status_values:
                self.status_values[key].config(text=val)
    
    def update_time(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
    
    def blink_status(self):
        current = self.status_dot.cget("fg")
        new_color = self.colors["bg_panel"] if current == self.colors["nominal"] else self.colors["nominal"]
        self.status_dot.config(fg=new_color)
    
    def update_all(self):
        try:
            self.update_time()
            self.update_thermal()
            self.update_cpu()
            self.update_memory()
            self.update_storage()
            self.update_network()
            self.update_processes()
            self.update_system_status()
            self.blink_status()
        except Exception as e:
            print(f"Update error: {e}")
        
        # Schedule next update
        self.root.after(1000, self.update_all)


def main():
    root = tk.Tk()
    
    # Set icon if possible
    try:
        root.iconname("System Monitor")
    except:
        pass
    
    app = SystemCommandCenter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
