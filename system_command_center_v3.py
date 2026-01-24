#!/usr/bin/env python3
"""
SYSTEM COMMAND CENTER v3
Comprehensive monitoring dashboard for Intel Arc B580 + AMD Ryzen systems

Features:
- GPU temps via Intel PMT telemetry + frequency + VRAM + fans
- CPU usage + temp + per-core utilization
- NVMe temperature
- Memory (RAM + Swap)
- Disk I/O speeds
- Network I/O + WiFi signal strength
- Top processes

NOTE: Run with sudo for full functionality:
    sudo python3 system_command_center_v3.py
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
        self.root.title("⚡ SYSTEM COMMAND CENTER v3")
        self.root.configure(bg="#0a0a0f")
        
        # Make fullscreen-ish
        self.root.geometry("1400x950")
        self.root.minsize(1200, 850)
        
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
            "accent_teal": "#14b8a6",
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
        self.gpu_temp_history = [0] * 60
        self.net_rx_history = [0] * 60
        self.net_tx_history = [0] * 60
        self.disk_read_history = [0] * 60
        self.disk_write_history = [0] * 60
        
        self.last_net_rx = 0
        self.last_net_tx = 0
        self.last_net_time = time.time()
        
        self.last_disk_read = 0
        self.last_disk_write = 0
        self.last_disk_time = time.time()
        
        self.start_time = datetime.now()
        
        # Get CPU core count
        try:
            self.num_cores = int(subprocess.getoutput("nproc"))
        except:
            self.num_cores = 8
        
        self.last_core_stats = {}
        
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
        
        # Content area - 3 columns
        content = tk.Frame(main, bg=self.colors["bg_dark"])
        content.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left column
        left_col = tk.Frame(content, bg=self.colors["bg_dark"], width=420)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left_col.pack_propagate(False)
        
        # Middle column
        mid_col = tk.Frame(content, bg=self.colors["bg_dark"], width=420)
        mid_col.pack(side="left", fill="both", expand=False, padx=5)
        mid_col.pack_propagate(False)
        
        # Right column
        right_col = tk.Frame(content, bg=self.colors["bg_dark"])
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Left column panels
        self.create_gpu_panel(left_col)
        self.create_cpu_panel(left_col)
        
        # Middle column panels
        self.create_cpu_cores_panel(mid_col)
        self.create_memory_panel(mid_col)
        self.create_storage_panel(mid_col)
        
        # Right column panels
        self.create_system_status_panel(right_col)
        self.create_disk_io_panel(right_col)
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
            text="INTEL ARC B580 + AMD RYZEN 7 • FULL TELEMETRY",
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
        
        # Right side - Time
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
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        return content
    
    def create_gpu_panel(self, parent):
        """GPU monitoring panel"""
        content = self.create_panel(parent, "GPU — INTEL ARC B580", height=280)
        
        # Row 1: Temps
        row1 = tk.Frame(content, bg=self.colors["bg_panel"])
        row1.pack(fill="x", pady=(0, 8))
        
        # GPU Temp
        temp1_frame = tk.Frame(row1, bg=self.colors["bg_panel"])
        temp1_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(temp1_frame, text="GPU TEMP", font=("Monospace", 8),
                fg=self.colors["accent_blue"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.gpu_temp1_label = tk.Label(temp1_frame, text="--°C", font=("Monospace", 28, "bold"),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_temp1_label.pack(anchor="w")
        
        self.gpu_temp1_status = tk.Label(temp1_frame, text="● STANDBY", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_temp1_status.pack(anchor="w")
        
        # Hotspot Temp
        temp2_frame = tk.Frame(row1, bg=self.colors["bg_panel"])
        temp2_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(temp2_frame, text="HOTSPOT", font=("Monospace", 8),
                fg=self.colors["accent_pink"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.gpu_temp2_label = tk.Label(temp2_frame, text="--°C", font=("Monospace", 28, "bold"),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_temp2_label.pack(anchor="w")
        
        self.gpu_temp2_status = tk.Label(temp2_frame, text="● STANDBY", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_temp2_status.pack(anchor="w")
        
        # GPU Frequency
        freq_frame = tk.Frame(row1, bg=self.colors["bg_panel"])
        freq_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(freq_frame, text="GPU CLOCK", font=("Monospace", 8),
                fg=self.colors["accent_cyan"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.gpu_freq_label = tk.Label(freq_frame, text="-- MHz", font=("Monospace", 20, "bold"),
                fg=self.colors["accent_cyan"], bg=self.colors["bg_panel"])
        self.gpu_freq_label.pack(anchor="e")
        
        self.gpu_freq_max = tk.Label(freq_frame, text="MAX: -- MHz", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_freq_max.pack(anchor="e")
        
        # Row 2: VRAM and Fans
        row2 = tk.Frame(content, bg=self.colors["bg_panel"])
        row2.pack(fill="x", pady=(5, 8))
        
        # VRAM
        vram_frame = tk.Frame(row2, bg=self.colors["bg_panel"])
        vram_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(vram_frame, text="VRAM USAGE", font=("Monospace", 8),
                fg=self.colors["accent_purple"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.vram_label = tk.Label(vram_frame, text="-- / -- GB", font=("Monospace", 14, "bold"),
                fg=self.colors["accent_purple"], bg=self.colors["bg_panel"])
        self.vram_label.pack(anchor="w")
        
        # VRAM bar
        self.vram_bar_frame = tk.Frame(vram_frame, bg=self.colors["bg_card"], height=8, width=150)
        self.vram_bar_frame.pack(anchor="w", pady=(3, 0))
        self.vram_bar_frame.pack_propagate(False)
        
        self.vram_bar = tk.Frame(self.vram_bar_frame, bg=self.colors["accent_purple"], width=0)
        self.vram_bar.pack(side="left", fill="y")
        
        # Fans
        fan_frame = tk.Frame(row2, bg=self.colors["bg_panel"])
        fan_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(fan_frame, text="GPU FANS", font=("Monospace", 8),
                fg=self.colors["accent_teal"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.fan_label = tk.Label(fan_frame, text="0 RPM", font=("Monospace", 14, "bold"),
                fg=self.colors["accent_teal"], bg=self.colors["bg_panel"])
        self.fan_label.pack(anchor="e")
        
        self.fan_status = tk.Label(fan_frame, text="● IDLE", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.fan_status.pack(anchor="e")
        
        # Thermal graph
        tk.Label(content, text="GPU THERMAL HISTORY (60s)", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"]).pack(anchor="w", pady=(5, 2))
        
        self.gpu_temp_canvas = tk.Canvas(content, bg=self.colors["bg_card"], height=50, highlightthickness=0)
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
        
        tk.Label(usage_frame, text="UTILIZATION", font=("Monospace", 8),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.cpu_percent_label = tk.Label(usage_frame, text="0%", font=("Monospace", 28, "bold"),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"])
        self.cpu_percent_label.pack(anchor="w")
        
        # CPU Temp
        temp_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        temp_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(temp_frame, text="CPU TEMP", font=("Monospace", 8),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.cpu_temp_label = tk.Label(temp_frame, text="--°C", font=("Monospace", 28, "bold"),
                fg=self.colors["nominal"], bg=self.colors["bg_panel"])
        self.cpu_temp_label.pack(anchor="w")
        
        self.cpu_temp_status = tk.Label(temp_frame, text="● NOMINAL", font=("Monospace", 8),
                fg=self.colors["nominal"], bg=self.colors["bg_panel"])
        self.cpu_temp_status.pack(anchor="w")
        
        # NVMe Temp
        nvme_frame = tk.Frame(top_row, bg=self.colors["bg_panel"])
        nvme_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(nvme_frame, text="NVMe TEMP", font=("Monospace", 8),
                fg=self.colors["accent_yellow"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.nvme_temp_label = tk.Label(nvme_frame, text="--°C", font=("Monospace", 20, "bold"),
                fg=self.colors["accent_yellow"], bg=self.colors["bg_panel"])
        self.nvme_temp_label.pack(anchor="e")
        
        self.nvme_status = tk.Label(nvme_frame, text="● NOMINAL", font=("Monospace", 8),
                fg=self.colors["nominal"], bg=self.colors["bg_panel"])
        self.nvme_status.pack(anchor="e")
        
        # CPU Info row
        info_row = tk.Frame(content, bg=self.colors["bg_panel"])
        info_row.pack(fill="x", pady=(10, 5))
        
        self.cpu_freq_label = tk.Label(info_row, text="0 MHz", font=("Monospace", 11, "bold"),
                fg=self.colors["text_normal"], bg=self.colors["bg_panel"])
        self.cpu_freq_label.pack(side="left")
        
        self.cpu_cores_label = tk.Label(info_row, text="0 cores / 0 threads", font=("Monospace", 9),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.cpu_cores_label.pack(side="right")
        
        # CPU Graph
        self.cpu_canvas = tk.Canvas(content, bg=self.colors["bg_card"], height=45, highlightthickness=0)
        self.cpu_canvas.pack(fill="x", pady=(5, 0))
    
    def create_cpu_cores_panel(self, parent):
        """Per-core CPU utilization"""
        content = self.create_panel(parent, "CPU CORE UTILIZATION", height=200)
        
        self.core_bars = []
        self.core_labels = []
        
        # Create grid of core indicators
        cores_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        cores_frame.pack(fill="both", expand=True)
        
        cols = 4  # 4 columns
        rows = (self.num_cores + cols - 1) // cols
        
        for i in range(self.num_cores):
            row = i // cols
            col = i % cols
            
            core_frame = tk.Frame(cores_frame, bg=self.colors["bg_panel"])
            core_frame.grid(row=row, column=col, padx=5, pady=3, sticky="ew")
            cores_frame.columnconfigure(col, weight=1)
            
            # Core label
            label = tk.Label(core_frame, text=f"C{i}", font=("Monospace", 8),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"], width=3)
            label.pack(side="left")
            
            # Bar frame
            bar_frame = tk.Frame(core_frame, bg=self.colors["bg_card"], height=16)
            bar_frame.pack(side="left", fill="x", expand=True, padx=(3, 3))
            bar_frame.pack_propagate(False)
            
            bar = tk.Frame(bar_frame, bg=self.colors["accent_green"], width=0)
            bar.pack(side="left", fill="y")
            
            # Percentage
            pct_label = tk.Label(core_frame, text="0%", font=("Monospace", 8),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"], width=4)
            pct_label.pack(side="right")
            
            self.core_bars.append((bar_frame, bar))
            self.core_labels.append(pct_label)
    
    def create_memory_panel(self, parent):
        """Memory panel"""
        content = self.create_panel(parent, "MEMORY ALLOCATION", height=130)
        
        # RAM
        ram_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        ram_frame.pack(fill="x", pady=(0, 10))
        
        ram_header = tk.Frame(ram_frame, bg=self.colors["bg_panel"])
        ram_header.pack(fill="x")
        
        tk.Label(ram_header, text="RAM", font=("Monospace", 10, "bold"),
                fg=self.colors["accent_purple"], bg=self.colors["bg_panel"]).pack(side="left")
        
        self.ram_percent = tk.Label(ram_header, text="0%", font=("Monospace", 10, "bold"),
                fg=self.colors["text_bright"], bg=self.colors["bg_panel"])
        self.ram_percent.pack(side="right")
        
        self.ram_bar_frame = tk.Frame(ram_frame, bg=self.colors["bg_card"], height=18)
        self.ram_bar_frame.pack(fill="x", pady=(4, 0))
        self.ram_bar_frame.pack_propagate(False)
        
        self.ram_bar = tk.Frame(self.ram_bar_frame, bg=self.colors["accent_purple"], width=0)
        self.ram_bar.pack(side="left", fill="y")
        
        self.ram_details = tk.Label(ram_frame, text="0 GB / 0 GB", font=("Monospace", 9),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.ram_details.pack(anchor="w", pady=(2, 0))
        
        # Swap
        swap_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        swap_frame.pack(fill="x")
        
        swap_header = tk.Frame(swap_frame, bg=self.colors["bg_panel"])
        swap_header.pack(fill="x")
        
        tk.Label(swap_header, text="SWAP", font=("Monospace", 10, "bold"),
                fg=self.colors["accent_yellow"], bg=self.colors["bg_panel"]).pack(side="left")
        
        self.swap_percent = tk.Label(swap_header, text="0%", font=("Monospace", 10, "bold"),
                fg=self.colors["text_bright"], bg=self.colors["bg_panel"])
        self.swap_percent.pack(side="right")
        
        self.swap_bar_frame = tk.Frame(swap_frame, bg=self.colors["bg_card"], height=12)
        self.swap_bar_frame.pack(fill="x", pady=(4, 0))
        self.swap_bar_frame.pack_propagate(False)
        
        self.swap_bar = tk.Frame(self.swap_bar_frame, bg=self.colors["accent_yellow"], width=0)
        self.swap_bar.pack(side="left", fill="y")
        
        self.swap_details = tk.Label(swap_frame, text="0 GB / 0 GB", font=("Monospace", 9),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.swap_details.pack(anchor="w", pady=(2, 0))
    
    def create_storage_panel(self, parent):
        """Storage devices panel"""
        content = self.create_panel(parent, "STORAGE DEVICES", expand=True)
        
        self.storage_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.storage_frame.pack(fill="both", expand=True)
    
    def create_system_status_panel(self, parent):
        """System status overview"""
        content = self.create_panel(parent, "SYSTEM STATUS", height=85)
        
        grid = tk.Frame(content, bg=self.colors["bg_panel"])
        grid.pack(fill="both", expand=True)
        
        status_items = [
            ("UPTIME", "uptime", self.colors["accent_cyan"]),
            ("PROCS", "procs", self.colors["accent_green"]),
            ("LOAD", "load", self.colors["accent_orange"]),
            ("THREADS", "threads", self.colors["accent_pink"]),
            ("WIFI", "wifi", self.colors["accent_teal"]),
        ]
        
        self.status_values = {}
        
        for i, (label, key, color) in enumerate(status_items):
            frame = tk.Frame(grid, bg=self.colors["bg_panel"])
            frame.pack(side="left", expand=True, fill="both", padx=3)
            
            tk.Label(frame, text=label, font=("Monospace", 8),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"]).pack()
            
            val_label = tk.Label(frame, text="--", font=("Monospace", 14, "bold"),
                    fg=color, bg=self.colors["bg_panel"])
            val_label.pack()
            self.status_values[key] = val_label
    
    def create_disk_io_panel(self, parent):
        """Disk I/O panel"""
        content = self.create_panel(parent, "DISK I/O", height=120)
        
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        # Read
        read_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        read_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(read_frame, text="▼ READ", font=("Monospace", 9),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.disk_read_label = tk.Label(read_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"])
        self.disk_read_label.pack(anchor="w")
        
        # Write
        write_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        write_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(write_frame, text="▲ WRITE", font=("Monospace", 9),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.disk_write_label = tk.Label(write_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"])
        self.disk_write_label.pack(anchor="e")
        
        # Graph
        self.disk_canvas = tk.Canvas(content, bg=self.colors["bg_card"], height=40, highlightthickness=0)
        self.disk_canvas.pack(fill="x", pady=(8, 0))
    
    def create_network_panel(self, parent):
        """Network panel"""
        content = self.create_panel(parent, "NETWORK I/O", height=120)
        
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        # Download
        dl_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        dl_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(dl_frame, text="▼ DOWNLOAD", font=("Monospace", 9),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.net_dl_label = tk.Label(dl_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"])
        self.net_dl_label.pack(anchor="w")
        
        # Upload
        ul_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        ul_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(ul_frame, text="▲ UPLOAD", font=("Monospace", 9),
                fg=self.colors["accent_red"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.net_ul_label = tk.Label(ul_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_red"], bg=self.colors["bg_panel"])
        self.net_ul_label.pack(anchor="e")
        
        # Graph
        self.net_canvas = tk.Canvas(content, bg=self.colors["bg_card"], height=40, highlightthickness=0)
        self.net_canvas.pack(fill="x", pady=(8, 0))
    
    def create_processes_panel(self, parent):
        """Top processes panel"""
        content = self.create_panel(parent, "TOP PROCESSES", expand=True)
        
        # Header
        header = tk.Frame(content, bg=self.colors["bg_panel"])
        header.pack(fill="x")
        
        cols = [("PROCESS", 25), ("CPU%", 7), ("MEM%", 7), ("PID", 8)]
        for text, width in cols:
            tk.Label(header, text=text, font=("Monospace", 8, "bold"),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"],
                    width=width, anchor="w").pack(side="left")
        
        # Separator
        tk.Frame(content, bg=self.colors["border"], height=1).pack(fill="x", pady=4)
        
        # Process list
        self.process_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.process_frame.pack(fill="both", expand=True)
        
        self.process_labels = []
        for i in range(10):
            row = tk.Frame(self.process_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=1)
            
            labels = []
            widths = [25, 7, 7, 8]
            for j, w in enumerate(widths):
                lbl = tk.Label(row, text="--", font=("Monospace", 9),
                        fg=self.colors["text_normal"] if j == 0 else self.colors["text_dim"],
                        bg=self.colors["bg_panel"], width=w, anchor="w")
                lbl.pack(side="left")
                labels.append(lbl)
            self.process_labels.append(labels)
    
    # ==================== DATA FETCHING ====================
    
    def get_gpu_temps(self):
        """Get GPU temps from Intel PMT telemetry"""
        if not self.has_root:
            return None, None
        try:
            with open('/sys/class/intel_pmt/telem2/telem', 'rb') as f:
                data = f.read()
                temp1 = struct.unpack('<I', data[0xa4:0xa8])[0]
                temp2 = struct.unpack('<I', data[0xa8:0xac])[0]
                if 0 < temp1 < 120 and 0 < temp2 < 120:
                    return temp1, temp2
            return None, None
        except:
            return None, None
    
    def get_gpu_frequency(self):
        """Get GPU frequency"""
        try:
            cur = int(Path("/sys/class/drm/card1/device/tile0/gt0/freq0/act_freq").read_text().strip())
            max_f = int(Path("/sys/class/drm/card1/device/tile0/gt0/freq0/max_freq").read_text().strip())
            return cur, max_f
        except:
            return None, None
    
    def get_gpu_vram(self):
        """Get GPU VRAM usage"""
        try:
            used = int(Path("/sys/class/drm/card1/device/mem_info_vram_used").read_text().strip())
            total = int(Path("/sys/class/drm/card1/device/mem_info_vram_total").read_text().strip())
            return used, total
        except:
            return None, None
    
    def get_gpu_fans(self):
        """Get GPU fan speeds"""
        try:
            fans = []
            for i in range(1, 4):
                try:
                    rpm = int(Path(f"/sys/class/hwmon/hwmon3/fan{i}_input").read_text().strip())
                    fans.append(rpm)
                except:
                    pass
            return max(fans) if fans else 0
        except:
            return 0
    
    def get_cpu_temp(self):
        """Get CPU temp from k10temp"""
        try:
            return int(Path("/sys/class/hwmon/hwmon2/temp1_input").read_text().strip()) / 1000
        except:
            return None
    
    def get_nvme_temp(self):
        """Get NVMe temperature"""
        try:
            return int(Path("/sys/class/hwmon/hwmon1/temp1_input").read_text().strip()) / 1000
        except:
            return None
    
    def get_cpu_usage(self):
        """Get total CPU usage"""
        try:
            parts = Path("/proc/stat").read_text().split('\n')[0].split()
            idle = int(parts[4])
            total = sum(int(p) for p in parts[1:])
            
            if hasattr(self, 'last_cpu_idle'):
                d_idle = idle - self.last_cpu_idle
                d_total = total - self.last_cpu_total
                usage = 100 * (1 - d_idle / d_total) if d_total > 0 else 0
            else:
                usage = 0
            
            self.last_cpu_idle = idle
            self.last_cpu_total = total
            return max(0, min(100, usage))
        except:
            return 0
    
    def get_per_core_usage(self):
        """Get per-core CPU usage"""
        try:
            lines = Path("/proc/stat").read_text().split('\n')
            usages = []
            
            for i in range(self.num_cores):
                line = lines[i + 1]  # cpu0 is line 1, etc
                parts = line.split()
                idle = int(parts[4])
                total = sum(int(p) for p in parts[1:])
                
                key = f"core{i}"
                if key in self.last_core_stats:
                    d_idle = idle - self.last_core_stats[key]['idle']
                    d_total = total - self.last_core_stats[key]['total']
                    usage = 100 * (1 - d_idle / d_total) if d_total > 0 else 0
                else:
                    usage = 0
                
                self.last_core_stats[key] = {'idle': idle, 'total': total}
                usages.append(max(0, min(100, usage)))
            
            return usages
        except:
            return [0] * self.num_cores
    
    def get_cpu_freq(self):
        """Get average CPU frequency"""
        try:
            freqs = []
            for line in Path("/proc/cpuinfo").read_text().split('\n'):
                if 'MHz' in line:
                    match = re.search(r':\s*(\d+)', line)
                    if match:
                        freqs.append(int(float(match.group(1))))
            return int(sum(freqs) / len(freqs)) if freqs else 0
        except:
            return 0
    
    def get_cpu_info(self):
        """Get CPU core/thread count"""
        try:
            threads = int(subprocess.getoutput("grep -c 'processor' /proc/cpuinfo"))
            physical = subprocess.getoutput("grep 'cpu cores' /proc/cpuinfo | head -1")
            match = re.search(r'(\d+)', physical)
            cores = int(match.group(1)) if match else threads // 2
            return cores, threads
        except:
            return 0, 0
    
    def get_memory_info(self):
        """Get RAM and swap usage"""
        try:
            lines = subprocess.getoutput("free -b").split('\n')
            mem = lines[1].split()
            swap = lines[2].split()
            return {
                'mem_total': int(mem[1]), 'mem_used': int(mem[2]),
                'mem_percent': int(mem[2]) / int(mem[1]) * 100 if int(mem[1]) > 0 else 0,
                'swap_total': int(swap[1]), 'swap_used': int(swap[2]),
                'swap_percent': int(swap[2]) / int(swap[1]) * 100 if int(swap[1]) > 0 else 0
            }
        except:
            return None
    
    def get_storage_info(self):
        """Get mounted storage devices"""
        try:
            output = subprocess.getoutput("df -B1 -x tmpfs -x devtmpfs -x squashfs -x overlay 2>/dev/null | tail -n +2")
            disks = []
            seen = set()
            for line in output.strip().split('\n'):
                if line:
                    p = line.split()
                    if len(p) >= 6 and p[5] not in seen:
                        seen.add(p[5])
                        disks.append({
                            'device': p[0].split('/')[-1],
                            'total': int(p[1]), 'used': int(p[2]),
                            'mount': p[5], 'percent': int(p[4].replace('%', ''))
                        })
            return disks
        except:
            return []
    
    def get_disk_io(self):
        """Get disk read/write speeds"""
        try:
            stats = Path("/proc/diskstats").read_text()
            read_bytes = 0
            write_bytes = 0
            
            for line in stats.split('\n'):
                parts = line.split()
                if len(parts) >= 14 and parts[2].startswith('nvme'):
                    # sectors read/written * 512 bytes
                    read_bytes += int(parts[5]) * 512
                    write_bytes += int(parts[9]) * 512
            
            now = time.time()
            elapsed = now - self.last_disk_time
            
            read_speed = (read_bytes - self.last_disk_read) / elapsed if elapsed > 0 and self.last_disk_read > 0 else 0
            write_speed = (write_bytes - self.last_disk_write) / elapsed if elapsed > 0 and self.last_disk_write > 0 else 0
            
            self.last_disk_read = read_bytes
            self.last_disk_write = write_bytes
            self.last_disk_time = now
            
            return max(0, read_speed), max(0, write_speed)
        except:
            return 0, 0
    
    def get_network_speed(self):
        """Get network speeds"""
        try:
            rx_total = 0
            tx_total = 0
            
            for iface in Path("/sys/class/net").iterdir():
                if iface.name not in ('lo', 'docker0') and not iface.name.startswith('veth'):
                    try:
                        rx_total += int((iface / "statistics/rx_bytes").read_text().strip())
                        tx_total += int((iface / "statistics/tx_bytes").read_text().strip())
                    except:
                        pass
            
            now = time.time()
            elapsed = now - self.last_net_time
            
            rx_speed = (rx_total - self.last_net_rx) / elapsed if elapsed > 0 and self.last_net_rx > 0 else 0
            tx_speed = (tx_total - self.last_net_tx) / elapsed if elapsed > 0 and self.last_net_tx > 0 else 0
            
            self.last_net_rx = rx_total
            self.last_net_tx = tx_total
            self.last_net_time = now
            
            return max(0, rx_speed), max(0, tx_speed)
        except:
            return 0, 0
    
    def get_wifi_signal(self):
        """Get WiFi signal strength"""
        try:
            output = subprocess.getoutput("cat /proc/net/wireless 2>/dev/null")
            for line in output.split('\n'):
                if 'wl' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        # Signal level (typically -30 to -90 dBm)
                        signal = int(float(parts[3].replace('.', '')))
                        # Convert to percentage (rough approximation)
                        quality = min(100, max(0, 2 * (signal + 100)))
                        return f"{quality}%"
            return "N/A"
        except:
            return "N/A"
    
    def get_top_processes(self):
        """Get top processes by CPU"""
        try:
            output = subprocess.getoutput("ps aux --sort=-%cpu | head -11 | tail -10")
            procs = []
            for line in output.strip().split('\n'):
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    name = parts[10].split()[0].split('/')[-1][:22]
                    procs.append({'name': name, 'cpu': parts[2], 'mem': parts[3], 'pid': parts[1]})
            return procs
        except:
            return []
    
    def get_system_stats(self):
        """Get system stats"""
        try:
            # Uptime
            uptime_sec = float(Path("/proc/uptime").read_text().split()[0])
            days = int(uptime_sec // 86400)
            hours = int((uptime_sec % 86400) // 3600)
            mins = int((uptime_sec % 3600) // 60)
            uptime = f"{days}d{hours}h" if days > 0 else f"{hours}h{mins}m"
            
            # Processes/threads
            procs = 0
            threads = 0
            for p in Path("/proc").iterdir():
                if p.name.isdigit():
                    procs += 1
                    try:
                        threads += len(list((p / "task").iterdir()))
                    except:
                        pass
            
            load = Path("/proc/loadavg").read_text().split()[0]
            wifi = self.get_wifi_signal()
            
            return {'uptime': uptime, 'procs': str(procs), 'threads': str(threads), 'load': load, 'wifi': wifi}
        except:
            return {'uptime': '--', 'procs': '--', 'threads': '--', 'load': '--', 'wifi': '--'}
    
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
        
        for i in range(1, 4):
            y = h * i / 4
            canvas.create_line(0, y, w, y, fill=self.colors["grid_line"], dash=(2, 4))
        
        if len(data) > 1 and max_val > 0:
            points = [(w * i / (len(data) - 1), h - h * min(v, max_val) / max_val) for i, v in enumerate(data)]
            canvas.create_polygon([(0, h)] + points + [(w, h)], fill=color, stipple="gray25", outline="")
            for i in range(len(points) - 1):
                canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=2)
    
    def draw_dual_graph(self, canvas, data1, color1, data2, color2, max_val=100):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w <= 1:
            return
        
        for i in range(1, 4):
            y = h * i / 4
            canvas.create_line(0, y, w, y, fill=self.colors["grid_line"], dash=(2, 4))
        
        for data, color in [(data1, color1), (data2, color2)]:
            if len(data) > 1 and max_val > 0:
                points = [(w * i / (len(data) - 1), h - h * min(v, max_val) / max_val) for i, v in enumerate(data)]
                for i in range(len(points) - 1):
                    canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=2)
    
    # ==================== UI UPDATES ====================
    
    def update_gpu(self):
        # Temps
        t1, t2 = self.get_gpu_temps()
        if t1 is not None:
            self.gpu_temp1_label.config(text=f"{t1}°C")
            c, s = self.get_temp_color_status(t1, (55, 80))
            self.gpu_temp1_label.config(fg=c)
            self.gpu_temp1_status.config(text=s, fg=c)
            self.gpu_temp_history.pop(0)
            self.gpu_temp_history.append(t1)
        else:
            self.gpu_temp1_label.config(text="--°C", fg=self.colors["text_dim"])
            self.gpu_temp1_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
        if t2 is not None:
            self.gpu_temp2_label.config(text=f"{t2}°C")
            c, s = self.get_temp_color_status(t2, (60, 85))
            self.gpu_temp2_label.config(fg=c)
            self.gpu_temp2_status.config(text=s, fg=c)
        else:
            self.gpu_temp2_label.config(text="--°C", fg=self.colors["text_dim"])
            self.gpu_temp2_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
        # Frequency
        cur, max_f = self.get_gpu_frequency()
        if cur is not None:
            self.gpu_freq_label.config(text=f"{cur} MHz")
            self.gpu_freq_max.config(text=f"MAX: {max_f} MHz")
        
        # VRAM
        used, total = self.get_gpu_vram()
        if used is not None:
            used_gb = used / (1024**3)
            total_gb = total / (1024**3)
            pct = used / total * 100 if total > 0 else 0
            self.vram_label.config(text=f"{used_gb:.1f} / {total_gb:.0f} GB")
            bar_w = int(150 * pct / 100)
            self.vram_bar.config(width=max(0, bar_w))
        else:
            self.vram_label.config(text="-- / -- GB")
        
        # Fans
        rpm = self.get_gpu_fans()
        self.fan_label.config(text=f"{rpm} RPM")
        if rpm > 0:
            self.fan_status.config(text="● ACTIVE", fg=self.colors["accent_teal"])
        else:
            self.fan_status.config(text="● IDLE", fg=self.colors["text_dim"])
        
        # Graph
        self.draw_graph(self.gpu_temp_canvas, self.gpu_temp_history, self.colors["accent_blue"], 100)
    
    def update_cpu(self):
        usage = self.get_cpu_usage()
        temp = self.get_cpu_temp()
        nvme_temp = self.get_nvme_temp()
        freq = self.get_cpu_freq()
        cores, threads = self.get_cpu_info()
        
        self.cpu_history.pop(0)
        self.cpu_history.append(usage)
        
        # Usage
        if usage < 50:
            color = self.colors["accent_green"]
        elif usage < 80:
            color = self.colors["warning"]
        else:
            color = self.colors["critical"]
        self.cpu_percent_label.config(text=f"{usage:.0f}%", fg=color)
        
        # CPU Temp
        if temp is not None:
            self.cpu_temp_label.config(text=f"{temp:.0f}°C")
            c, s = self.get_temp_color_status(temp, (55, 75))
            self.cpu_temp_label.config(fg=c)
            self.cpu_temp_status.config(text=s, fg=c)
        
        # NVMe Temp
        if nvme_temp is not None:
            self.nvme_temp_label.config(text=f"{nvme_temp:.0f}°C")
            c, s = self.get_temp_color_status(nvme_temp, (50, 70))
            self.nvme_temp_label.config(fg=c)
            self.nvme_status.config(text=s, fg=c)
        
        # Info
        self.cpu_freq_label.config(text=f"{freq} MHz")
        self.cpu_cores_label.config(text=f"{cores} cores / {threads} threads")
        
        # Graph
        self.draw_graph(self.cpu_canvas, self.cpu_history, color)
    
    def update_cpu_cores(self):
        usages = self.get_per_core_usage()
        
        for i, usage in enumerate(usages):
            if i < len(self.core_bars):
                bar_frame, bar = self.core_bars[i]
                
                # Color based on usage
                if usage < 50:
                    color = self.colors["accent_green"]
                elif usage < 80:
                    color = self.colors["warning"]
                else:
                    color = self.colors["critical"]
                
                # Update bar
                bar_w = int(bar_frame.winfo_width() * usage / 100)
                bar.config(width=max(0, bar_w), bg=color)
                
                # Update label
                self.core_labels[i].config(text=f"{usage:.0f}%", fg=color)
    
    def update_memory(self):
        mem = self.get_memory_info()
        if mem:
            self.ram_percent.config(text=f"{mem['mem_percent']:.1f}%")
            self.ram_details.config(text=f"{self.format_bytes(mem['mem_used'])} / {self.format_bytes(mem['mem_total'])}")
            bar_w = int(self.ram_bar_frame.winfo_width() * mem['mem_percent'] / 100)
            self.ram_bar.config(width=max(0, bar_w))
            
            self.swap_percent.config(text=f"{mem['swap_percent']:.1f}%")
            self.swap_details.config(text=f"{self.format_bytes(mem['swap_used'])} / {self.format_bytes(mem['swap_total'])}")
            swap_w = int(self.swap_bar_frame.winfo_width() * mem['swap_percent'] / 100)
            self.swap_bar.config(width=max(0, swap_w))
    
    def update_storage(self):
        disks = self.get_storage_info()
        
        for w in self.storage_frame.winfo_children():
            w.destroy()
        
        for disk in disks[:4]:
            row = tk.Frame(self.storage_frame, bg=self.colors["bg_panel"])
            row.pack(fill="x", pady=2)
            
            mount = disk['mount'] if len(disk['mount']) <= 15 else disk['mount'][:12] + "..."
            tk.Label(row, text=mount, font=("Monospace", 9), fg=self.colors["text_normal"],
                    bg=self.colors["bg_panel"], width=15, anchor="w").pack(side="left")
            
            pct = disk['percent']
            color = self.colors["accent_green"] if pct < 70 else self.colors["warning"] if pct < 90 else self.colors["critical"]
            
            tk.Label(row, text=f"{pct}%", font=("Monospace", 9, "bold"), fg=color,
                    bg=self.colors["bg_panel"], width=5).pack(side="right")
            
            tk.Label(row, text=f"{self.format_bytes(disk['used'])}/{self.format_bytes(disk['total'])}",
                    font=("Monospace", 8), fg=self.colors["text_dim"],
                    bg=self.colors["bg_panel"]).pack(side="right", padx=5)
            
            bar_f = tk.Frame(row, bg=self.colors["bg_card"], height=10, width=60)
            bar_f.pack(side="right", padx=3)
            bar_f.pack_propagate(False)
            tk.Frame(bar_f, bg=color, width=int(60 * pct / 100)).pack(side="left", fill="y")
    
    def update_disk_io(self):
        read, write = self.get_disk_io()
        
        self.disk_read_label.config(text=self.format_speed(read))
        self.disk_write_label.config(text=self.format_speed(write))
        
        self.disk_read_history.pop(0)
        self.disk_read_history.append(read)
        self.disk_write_history.pop(0)
        self.disk_write_history.append(write)
        
        max_io = max(max(self.disk_read_history), max(self.disk_write_history), 1024)
        self.draw_dual_graph(self.disk_canvas, self.disk_read_history, self.colors["accent_green"],
                            self.disk_write_history, self.colors["accent_orange"], max_io)
    
    def update_network(self):
        rx, tx = self.get_network_speed()
        
        self.net_dl_label.config(text=self.format_speed(rx))
        self.net_ul_label.config(text=self.format_speed(tx))
        
        self.net_rx_history.pop(0)
        self.net_rx_history.append(rx)
        self.net_tx_history.pop(0)
        self.net_tx_history.append(tx)
        
        max_net = max(max(self.net_rx_history), max(self.net_tx_history), 1024)
        self.draw_dual_graph(self.net_canvas, self.net_rx_history, self.colors["accent_green"],
                            self.net_tx_history, self.colors["accent_red"], max_net)
    
    def update_processes(self):
        procs = self.get_top_processes()
        
        for i, labels in enumerate(self.process_labels):
            if i < len(procs):
                p = procs[i]
                labels[0].config(text=p['name'], fg=self.colors["text_normal"])
                
                try:
                    cpu = float(p['cpu'])
                    cpu_color = self.colors["critical"] if cpu > 50 else self.colors["warning"] if cpu > 20 else self.colors["text_dim"]
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
        new = self.colors["bg_panel"] if current == self.colors["nominal"] else self.colors["nominal"]
        self.status_dot.config(fg=new)
        self.root.after(800, self.blink_cycle)
    
    def update_all(self):
        try:
            self.update_time()
            self.update_gpu()
            self.update_cpu()
            self.update_cpu_cores()
            self.update_memory()
            self.update_storage()
            self.update_disk_io()
            self.update_network()
            self.update_processes()
            self.update_system_status()
        except Exception as e:
            print(f"Update error: {e}")
        
        self.root.after(1000, self.update_all)


def main():
    if os.geteuid() != 0:
        print("=" * 60)
        print("  NOTE: Run with sudo for GPU temperature monitoring")
        print("  sudo python3 system_command_center_v3.py")
        print("=" * 60)
        print()
    
    root = tk.Tk()
    app = SystemCommandCenter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
