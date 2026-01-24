#!/usr/bin/env python3
"""
SYSTEM COMMAND CENTER v4
Comprehensive monitoring dashboard for Intel Arc B580 + AMD Ryzen systems

Eye Candy Edition:
- Animated circular gauges for temps
- Color gradient bars
- Pulsing critical alerts
- Fullscreen mode (F11)
- Smooth animations
- Glowing effects

NOTE: Run with sudo for full functionality:
    sudo python3 system_command_center_v4.py
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import struct
import re
import os
import time
import math
import threading
from pathlib import Path
from datetime import datetime, timedelta


class SystemCommandCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ SYSTEM COMMAND CENTER v4")
        self.root.configure(bg="#0a0a0f")
        
        # Fullscreen toggle
        self.is_fullscreen = False
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        
        # Window size
        self.root.geometry("1450x950")
        self.root.minsize(1200, 850)
        
        # Color scheme
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
            "grid_line": "#1a1f26",
            "glow_blue": "#0066ff",
            "glow_red": "#ff0044",
            "glow_green": "#00ff66"
        }
        
        # Animation state
        self.pulse_state = 0
        self.gauge_animations = {}
        self.alert_flash = False
        self.scan_line_pos = 0
        
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
        
        # CPU cores
        try:
            self.num_cores = int(subprocess.getoutput("nproc"))
        except:
            self.num_cores = 8
        
        self.last_core_stats = {}
        
        # Root check
        self.has_root = os.geteuid() == 0
        
        # Current values for animations
        self.current_gpu_temp = 0
        self.current_cpu_temp = 0
        self.current_cpu_usage = 0
        self.is_critical = False
        
        self.setup_ui()
        self.animate()
        self.update_all()
    
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes("-fullscreen", self.is_fullscreen)
        return "break"
    
    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.root.attributes("-fullscreen", False)
        return "break"
    
    def setup_ui(self):
        # Main container
        main = tk.Frame(self.root, bg=self.colors["bg_dark"])
        main.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main)
        
        # Content - 3 columns
        content = tk.Frame(main, bg=self.colors["bg_dark"])
        content.pack(fill="both", expand=True, pady=(10, 0))
        
        # Left column
        left_col = tk.Frame(content, bg=self.colors["bg_dark"], width=450)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 5))
        left_col.pack_propagate(False)
        
        # Middle column
        mid_col = tk.Frame(content, bg=self.colors["bg_dark"], width=420)
        mid_col.pack(side="left", fill="both", expand=False, padx=5)
        mid_col.pack_propagate(False)
        
        # Right column
        right_col = tk.Frame(content, bg=self.colors["bg_dark"])
        right_col.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Left panels
        self.create_gpu_panel(left_col)
        self.create_cpu_panel(left_col)
        
        # Middle panels
        self.create_cpu_cores_panel(mid_col)
        self.create_memory_panel(mid_col)
        self.create_storage_panel(mid_col)
        
        # Right panels
        self.create_system_status_panel(right_col)
        self.create_disk_io_panel(right_col)
        self.create_network_panel(right_col)
        self.create_processes_panel(right_col)
    
    def create_header(self, parent):
        header = tk.Frame(parent, bg=self.colors["bg_panel"], height=75)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        # Scan line canvas (decorative)
        self.header_canvas = tk.Canvas(header, bg=self.colors["bg_panel"], height=75, highlightthickness=0)
        self.header_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Left - Title
        left = tk.Frame(header, bg=self.colors["bg_panel"])
        left.pack(side="left", fill="y", padx=15)
        
        title_frame = tk.Frame(left, bg=self.colors["bg_panel"])
        title_frame.pack(side="left", pady=10)
        
        title = tk.Label(
            title_frame,
            text="◆ SYSTEM COMMAND CENTER",
            font=("Monospace", 20, "bold"),
            fg=self.colors["accent_cyan"],
            bg=self.colors["bg_panel"]
        )
        title.pack(anchor="w")
        
        subtitle = tk.Label(
            title_frame,
            text="INTEL ARC B580 + AMD RYZEN 7 • FULL TELEMETRY • F11 FULLSCREEN",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg_panel"]
        )
        subtitle.pack(anchor="w")
        
        # Status
        status_frame = tk.Frame(left, bg=self.colors["bg_panel"])
        status_frame.pack(side="left", padx=(30, 0), pady=15)
        
        self.status_dot = tk.Label(
            status_frame, text="●", font=("Monospace", 16),
            fg=self.colors["nominal"], bg=self.colors["bg_panel"]
        )
        self.status_dot.pack(side="left")
        
        self.status_text = tk.Label(
            status_frame, text="ALL SYSTEMS NOMINAL", font=("Monospace", 11, "bold"),
            fg=self.colors["nominal"], bg=self.colors["bg_panel"]
        )
        self.status_text.pack(side="left", padx=(8, 0))
        
        if not self.has_root:
            tk.Label(
                status_frame, text="  ⚠ sudo required for GPU temps", font=("Monospace", 9),
                fg=self.colors["warning"], bg=self.colors["bg_panel"]
            ).pack(side="left", padx=(15, 0))
        
        # Right - Time
        right = tk.Frame(header, bg=self.colors["bg_panel"])
        right.pack(side="right", fill="y", padx=15)
        
        time_frame = tk.Frame(right, bg=self.colors["bg_panel"])
        time_frame.pack(side="right", pady=10)
        
        self.time_label = tk.Label(
            time_frame, text="00:00:00", font=("Monospace", 28, "bold"),
            fg=self.colors["text_bright"], bg=self.colors["bg_panel"]
        )
        self.time_label.pack(anchor="e")
        
        self.date_label = tk.Label(
            time_frame, text="", font=("Monospace", 10),
            fg=self.colors["text_dim"], bg=self.colors["bg_panel"]
        )
        self.date_label.pack(anchor="e")
        
        # Center - Host
        center = tk.Frame(header, bg=self.colors["bg_panel"])
        center.pack(side="right", fill="y", padx=30)
        
        hostname = subprocess.getoutput("hostname").strip()
        kernel = subprocess.getoutput("uname -r").strip()
        
        self.hostname_label = tk.Label(
            center, text=f"◈ {hostname.upper()}", font=("Monospace", 13, "bold"),
            fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]
        )
        self.hostname_label.pack(pady=(18, 0))
        
        tk.Label(
            center, text=f"KERNEL {kernel}", font=("Monospace", 9),
            fg=self.colors["text_dim"], bg=self.colors["bg_panel"]
        ).pack()
    
    def create_panel(self, parent, title, height=None, expand=False):
        container = tk.Frame(parent, bg=self.colors["bg_dark"])
        container.pack(fill="both", expand=expand, pady=(0, 8))
        
        panel = tk.Frame(
            container, bg=self.colors["bg_panel"],
            highlightbackground=self.colors["border"], highlightthickness=1
        )
        panel.pack(fill="both", expand=True)
        
        if height:
            panel.configure(height=height)
            panel.pack_propagate(False)
        
        # Title bar with gradient effect
        title_bar = tk.Canvas(panel, bg=self.colors["bg_card"], height=30, highlightthickness=0)
        title_bar.pack(fill="x")
        
        # Draw gradient on title
        title_bar.create_text(
            12, 15, text=f"▸ {title}", font=("Monospace", 10, "bold"),
            fill=self.colors["accent_cyan"], anchor="w"
        )
        
        content = tk.Frame(panel, bg=self.colors["bg_panel"])
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        return content
    
    def create_gauge(self, parent, size=100, label="", color=None):
        """Create an animated circular gauge"""
        if color is None:
            color = self.colors["accent_cyan"]
        
        frame = tk.Frame(parent, bg=self.colors["bg_panel"])
        
        canvas = tk.Canvas(
            frame, width=size, height=size,
            bg=self.colors["bg_panel"], highlightthickness=0
        )
        canvas.pack()
        
        # Label
        lbl = tk.Label(
            frame, text=label, font=("Monospace", 8),
            fg=self.colors["text_dim"], bg=self.colors["bg_panel"]
        )
        lbl.pack()
        
        return frame, canvas
    
    def draw_gauge(self, canvas, value, max_val=100, color=None, label=""):
        """Draw an animated circular gauge with glow effect"""
        canvas.delete("all")
        
        size = canvas.winfo_width()
        if size <= 1:
            size = 100
        
        cx, cy = size // 2, size // 2
        radius = size // 2 - 10
        inner_radius = radius - 12
        
        if color is None:
            color = self.colors["accent_cyan"]
        
        # Determine color based on value
        pct = value / max_val if max_val > 0 else 0
        if pct > 0.85:
            color = self.colors["critical"]
            glow = self.colors["glow_red"]
        elif pct > 0.65:
            color = self.colors["warning"]
            glow = self.colors["accent_orange"]
        else:
            color = self.colors["nominal"]
            glow = self.colors["glow_green"]
        
        # Background arc
        canvas.create_arc(
            cx - radius, cy - radius, cx + radius, cy + radius,
            start=225, extent=-270, style="arc",
            outline=self.colors["bg_card"], width=10
        )
        
        # Glow effect (outer)
        if pct > 0:
            extent = -270 * pct
            canvas.create_arc(
                cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2,
                start=225, extent=extent, style="arc",
                outline=glow, width=2
            )
        
        # Value arc
        if pct > 0:
            extent = -270 * pct
            canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=225, extent=extent, style="arc",
                outline=color, width=10
            )
        
        # Inner circle
        canvas.create_oval(
            cx - inner_radius, cy - inner_radius,
            cx + inner_radius, cy + inner_radius,
            fill=self.colors["bg_card"], outline=""
        )
        
        # Value text
        canvas.create_text(
            cx, cy - 5, text=f"{value:.0f}",
            font=("Monospace", 18, "bold"), fill=color
        )
        
        # Unit text
        canvas.create_text(
            cx, cy + 18, text=label,
            font=("Monospace", 8), fill=self.colors["text_dim"]
        )
    
    def create_gpu_panel(self, parent):
        content = self.create_panel(parent, "GPU — INTEL ARC B580", height=300)
        
        # Gauges row
        gauges_row = tk.Frame(content, bg=self.colors["bg_panel"])
        gauges_row.pack(fill="x", pady=(0, 5))
        
        # GPU Temp gauge
        gauge_frame1 = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        gauge_frame1.pack(side="left", expand=True)
        
        tk.Label(gauge_frame1, text="GPU TEMP", font=("Monospace", 8),
                fg=self.colors["accent_blue"], bg=self.colors["bg_panel"]).pack()
        
        self.gpu_temp_canvas = tk.Canvas(
            gauge_frame1, width=100, height=100,
            bg=self.colors["bg_panel"], highlightthickness=0
        )
        self.gpu_temp_canvas.pack()
        
        self.gpu_temp_status = tk.Label(gauge_frame1, text="● STANDBY", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_temp_status.pack()
        
        # Hotspot gauge
        gauge_frame2 = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        gauge_frame2.pack(side="left", expand=True)
        
        tk.Label(gauge_frame2, text="HOTSPOT", font=("Monospace", 8),
                fg=self.colors["accent_pink"], bg=self.colors["bg_panel"]).pack()
        
        self.gpu_hotspot_canvas = tk.Canvas(
            gauge_frame2, width=100, height=100,
            bg=self.colors["bg_panel"], highlightthickness=0
        )
        self.gpu_hotspot_canvas.pack()
        
        self.gpu_hotspot_status = tk.Label(gauge_frame2, text="● STANDBY", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_hotspot_status.pack()
        
        # Frequency display
        freq_frame = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        freq_frame.pack(side="right", expand=True, fill="y")
        
        tk.Label(freq_frame, text="GPU CLOCK", font=("Monospace", 8),
                fg=self.colors["accent_cyan"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.gpu_freq_label = tk.Label(freq_frame, text="-- MHz", font=("Monospace", 22, "bold"),
                fg=self.colors["accent_cyan"], bg=self.colors["bg_panel"])
        self.gpu_freq_label.pack(anchor="e")
        
        self.gpu_freq_max = tk.Label(freq_frame, text="MAX: --", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.gpu_freq_max.pack(anchor="e")
        
        # VRAM + Fans row
        row2 = tk.Frame(content, bg=self.colors["bg_panel"])
        row2.pack(fill="x", pady=(8, 5))
        
        # VRAM with gradient bar
        vram_frame = tk.Frame(row2, bg=self.colors["bg_panel"])
        vram_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(vram_frame, text="VRAM", font=("Monospace", 8),
                fg=self.colors["accent_purple"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.vram_label = tk.Label(vram_frame, text="-- / -- GB", font=("Monospace", 12, "bold"),
                fg=self.colors["accent_purple"], bg=self.colors["bg_panel"])
        self.vram_label.pack(anchor="w")
        
        self.vram_canvas = tk.Canvas(vram_frame, height=12, bg=self.colors["bg_card"], highlightthickness=0)
        self.vram_canvas.pack(fill="x", pady=(3, 0))
        
        # Fans
        fan_frame = tk.Frame(row2, bg=self.colors["bg_panel"])
        fan_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(fan_frame, text="FANS", font=("Monospace", 8),
                fg=self.colors["accent_teal"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.fan_label = tk.Label(fan_frame, text="0 RPM", font=("Monospace", 12, "bold"),
                fg=self.colors["accent_teal"], bg=self.colors["bg_panel"])
        self.fan_label.pack(anchor="e")
        
        self.fan_status = tk.Label(fan_frame, text="● IDLE", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.fan_status.pack(anchor="e")
        
        # Thermal graph
        tk.Label(content, text="THERMAL HISTORY", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"]).pack(anchor="w", pady=(5, 2))
        
        self.gpu_graph_canvas = tk.Canvas(content, height=45, bg=self.colors["bg_card"], highlightthickness=0)
        self.gpu_graph_canvas.pack(fill="x")
    
    def create_cpu_panel(self, parent):
        content = self.create_panel(parent, "CPU — AMD RYZEN 7", height=210)
        
        # Gauges row
        gauges_row = tk.Frame(content, bg=self.colors["bg_panel"])
        gauges_row.pack(fill="x")
        
        # CPU Usage gauge
        gauge_frame1 = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        gauge_frame1.pack(side="left", expand=True)
        
        tk.Label(gauge_frame1, text="UTILIZATION", font=("Monospace", 8),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack()
        
        self.cpu_usage_canvas = tk.Canvas(
            gauge_frame1, width=100, height=100,
            bg=self.colors["bg_panel"], highlightthickness=0
        )
        self.cpu_usage_canvas.pack()
        
        # CPU Temp gauge
        gauge_frame2 = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        gauge_frame2.pack(side="left", expand=True)
        
        tk.Label(gauge_frame2, text="CPU TEMP", font=("Monospace", 8),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack()
        
        self.cpu_temp_canvas = tk.Canvas(
            gauge_frame2, width=100, height=100,
            bg=self.colors["bg_panel"], highlightthickness=0
        )
        self.cpu_temp_canvas.pack()
        
        self.cpu_temp_status = tk.Label(gauge_frame2, text="● NOMINAL", font=("Monospace", 8),
                fg=self.colors["nominal"], bg=self.colors["bg_panel"])
        self.cpu_temp_status.pack()
        
        # NVMe + Info
        info_frame = tk.Frame(gauges_row, bg=self.colors["bg_panel"])
        info_frame.pack(side="right", expand=True, fill="y")
        
        tk.Label(info_frame, text="NVMe TEMP", font=("Monospace", 8),
                fg=self.colors["accent_yellow"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.nvme_temp_label = tk.Label(info_frame, text="--°C", font=("Monospace", 18, "bold"),
                fg=self.colors["accent_yellow"], bg=self.colors["bg_panel"])
        self.nvme_temp_label.pack(anchor="e")
        
        self.cpu_freq_label = tk.Label(info_frame, text="-- MHz", font=("Monospace", 10),
                fg=self.colors["text_normal"], bg=self.colors["bg_panel"])
        self.cpu_freq_label.pack(anchor="e", pady=(10, 0))
        
        self.cpu_cores_label = tk.Label(info_frame, text="-- cores", font=("Monospace", 8),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.cpu_cores_label.pack(anchor="e")
        
        # CPU Graph
        self.cpu_graph_canvas = tk.Canvas(content, height=40, bg=self.colors["bg_card"], highlightthickness=0)
        self.cpu_graph_canvas.pack(fill="x", pady=(8, 0))
    
    def create_cpu_cores_panel(self, parent):
        content = self.create_panel(parent, "CPU CORE UTILIZATION", height=200)
        
        self.core_bars = []
        self.core_labels = []
        self.core_canvases = []
        
        cores_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        cores_frame.pack(fill="both", expand=True)
        
        cols = 4
        
        for i in range(self.num_cores):
            row = i // cols
            col = i % cols
            
            core_frame = tk.Frame(cores_frame, bg=self.colors["bg_panel"])
            core_frame.grid(row=row, column=col, padx=4, pady=3, sticky="ew")
            cores_frame.columnconfigure(col, weight=1)
            
            label = tk.Label(core_frame, text=f"C{i}", font=("Monospace", 8),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"], width=3)
            label.pack(side="left")
            
            # Gradient bar canvas
            bar_canvas = tk.Canvas(core_frame, height=18, bg=self.colors["bg_card"], highlightthickness=0)
            bar_canvas.pack(side="left", fill="x", expand=True, padx=2)
            
            pct_label = tk.Label(core_frame, text="0%", font=("Monospace", 8),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"], width=4)
            pct_label.pack(side="right")
            
            self.core_canvases.append(bar_canvas)
            self.core_labels.append(pct_label)
    
    def draw_gradient_bar(self, canvas, value, max_val=100):
        """Draw a gradient progress bar"""
        canvas.delete("all")
        
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w <= 1:
            return
        
        pct = value / max_val if max_val > 0 else 0
        fill_width = int(w * pct)
        
        if fill_width > 0:
            # Create gradient effect
            if pct > 0.8:
                colors = ["#ff0040", "#ff4444", "#ff6666"]
            elif pct > 0.5:
                colors = ["#ff8c00", "#ffaa00", "#ffcc00"]
            else:
                colors = ["#00aa55", "#00ff88", "#44ffaa"]
            
            # Draw gradient segments
            seg_width = fill_width // 3 if fill_width > 3 else fill_width
            for i, color in enumerate(colors):
                x1 = i * seg_width
                x2 = min((i + 1) * seg_width, fill_width)
                if x2 > x1:
                    canvas.create_rectangle(x1, 2, x2, h - 2, fill=color, outline="")
            
            # Glow effect at the end
            if fill_width > 5:
                canvas.create_rectangle(
                    fill_width - 3, 0, fill_width, h,
                    fill=colors[-1], outline=""
                )
    
    def create_memory_panel(self, parent):
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
        
        self.ram_canvas = tk.Canvas(ram_frame, height=20, bg=self.colors["bg_card"], highlightthickness=0)
        self.ram_canvas.pack(fill="x", pady=(4, 0))
        
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
        
        self.swap_canvas = tk.Canvas(swap_frame, height=14, bg=self.colors["bg_card"], highlightthickness=0)
        self.swap_canvas.pack(fill="x", pady=(4, 0))
        
        self.swap_details = tk.Label(swap_frame, text="0 GB / 0 GB", font=("Monospace", 9),
                fg=self.colors["text_dim"], bg=self.colors["bg_panel"])
        self.swap_details.pack(anchor="w", pady=(2, 0))
    
    def create_storage_panel(self, parent):
        content = self.create_panel(parent, "STORAGE DEVICES", expand=True)
        
        self.storage_frame = tk.Frame(content, bg=self.colors["bg_panel"])
        self.storage_frame.pack(fill="both", expand=True)
    
    def create_system_status_panel(self, parent):
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
        content = self.create_panel(parent, "DISK I/O", height=120)
        
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        read_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        read_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(read_frame, text="▼ READ", font=("Monospace", 9),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.disk_read_label = tk.Label(read_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"])
        self.disk_read_label.pack(anchor="w")
        
        write_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        write_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(write_frame, text="▲ WRITE", font=("Monospace", 9),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.disk_write_label = tk.Label(write_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_orange"], bg=self.colors["bg_panel"])
        self.disk_write_label.pack(anchor="e")
        
        self.disk_canvas = tk.Canvas(content, height=40, bg=self.colors["bg_card"], highlightthickness=0)
        self.disk_canvas.pack(fill="x", pady=(8, 0))
    
    def create_network_panel(self, parent):
        content = self.create_panel(parent, "NETWORK I/O", height=120)
        
        stats = tk.Frame(content, bg=self.colors["bg_panel"])
        stats.pack(fill="x")
        
        dl_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        dl_frame.pack(side="left", expand=True, fill="x")
        
        tk.Label(dl_frame, text="▼ DOWNLOAD", font=("Monospace", 9),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"]).pack(anchor="w")
        
        self.net_dl_label = tk.Label(dl_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_green"], bg=self.colors["bg_panel"])
        self.net_dl_label.pack(anchor="w")
        
        ul_frame = tk.Frame(stats, bg=self.colors["bg_panel"])
        ul_frame.pack(side="right", expand=True, fill="x")
        
        tk.Label(ul_frame, text="▲ UPLOAD", font=("Monospace", 9),
                fg=self.colors["accent_red"], bg=self.colors["bg_panel"]).pack(anchor="e")
        
        self.net_ul_label = tk.Label(ul_frame, text="0 B/s", font=("Monospace", 16, "bold"),
                fg=self.colors["accent_red"], bg=self.colors["bg_panel"])
        self.net_ul_label.pack(anchor="e")
        
        self.net_canvas = tk.Canvas(content, height=40, bg=self.colors["bg_card"], highlightthickness=0)
        self.net_canvas.pack(fill="x", pady=(8, 0))
    
    def create_processes_panel(self, parent):
        content = self.create_panel(parent, "TOP PROCESSES", expand=True)
        
        header = tk.Frame(content, bg=self.colors["bg_panel"])
        header.pack(fill="x")
        
        cols = [("PROCESS", 25), ("CPU%", 7), ("MEM%", 7), ("PID", 8)]
        for text, width in cols:
            tk.Label(header, text=text, font=("Monospace", 8, "bold"),
                    fg=self.colors["text_dim"], bg=self.colors["bg_panel"],
                    width=width, anchor="w").pack(side="left")
        
        tk.Frame(content, bg=self.colors["border"], height=1).pack(fill="x", pady=4)
        
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
        if not self.has_root:
            return None, None
        try:
            with open('/sys/class/intel_pmt/telem2/telem', 'rb') as f:
                data = f.read()
                t1 = struct.unpack('<I', data[0xa4:0xa8])[0]
                t2 = struct.unpack('<I', data[0xa8:0xac])[0]
                if 0 < t1 < 120 and 0 < t2 < 120:
                    return t1, t2
            return None, None
        except:
            return None, None
    
    def get_gpu_frequency(self):
        try:
            cur = int(Path("/sys/class/drm/card1/device/tile0/gt0/freq0/act_freq").read_text().strip())
            max_f = int(Path("/sys/class/drm/card1/device/tile0/gt0/freq0/max_freq").read_text().strip())
            return cur, max_f
        except:
            return None, None
    
    def get_gpu_vram(self):
        try:
            used = int(Path("/sys/class/drm/card1/device/mem_info_vram_used").read_text().strip())
            total = int(Path("/sys/class/drm/card1/device/mem_info_vram_total").read_text().strip())
            return used, total
        except:
            return None, None
    
    def get_gpu_fans(self):
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
        try:
            return int(Path("/sys/class/hwmon/hwmon2/temp1_input").read_text().strip()) / 1000
        except:
            return None
    
    def get_nvme_temp(self):
        try:
            return int(Path("/sys/class/hwmon/hwmon1/temp1_input").read_text().strip()) / 1000
        except:
            return None
    
    def get_cpu_usage(self):
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
        try:
            lines = Path("/proc/stat").read_text().split('\n')
            usages = []
            
            for i in range(self.num_cores):
                line = lines[i + 1]
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
        try:
            threads = int(subprocess.getoutput("grep -c 'processor' /proc/cpuinfo"))
            physical = subprocess.getoutput("grep 'cpu cores' /proc/cpuinfo | head -1")
            match = re.search(r'(\d+)', physical)
            cores = int(match.group(1)) if match else threads // 2
            return cores, threads
        except:
            return 0, 0
    
    def get_memory_info(self):
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
        try:
            stats = Path("/proc/diskstats").read_text()
            read_bytes = 0
            write_bytes = 0
            
            for line in stats.split('\n'):
                parts = line.split()
                if len(parts) >= 14 and parts[2].startswith('nvme'):
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
        try:
            output = subprocess.getoutput("cat /proc/net/wireless 2>/dev/null")
            for line in output.split('\n'):
                if 'wl' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        signal = int(float(parts[3].replace('.', '')))
                        quality = min(100, max(0, 2 * (signal + 100)))
                        return f"{quality}%"
            return "N/A"
        except:
            return "N/A"
    
    def get_top_processes(self):
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
        try:
            uptime_sec = float(Path("/proc/uptime").read_text().split()[0])
            days = int(uptime_sec // 86400)
            hours = int((uptime_sec % 86400) // 3600)
            mins = int((uptime_sec % 3600) // 60)
            uptime = f"{days}d{hours}h" if days > 0 else f"{hours}h{mins}m"
            
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
        
        # Grid
        for i in range(1, 4):
            y = h * i / 4
            canvas.create_line(0, y, w, y, fill=self.colors["grid_line"], dash=(2, 4))
        
        if len(data) > 1 and max_val > 0:
            points = [(w * i / (len(data) - 1), h - h * min(v, max_val) / max_val) for i, v in enumerate(data)]
            
            # Gradient fill
            canvas.create_polygon([(0, h)] + points + [(w, h)], fill=color, stipple="gray25", outline="")
            
            # Main line
            for i in range(len(points) - 1):
                canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=color, width=2)
            
            # Glow effect on recent data
            if len(points) > 5:
                for i in range(len(points) - 5, len(points) - 1):
                    canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                                      fill=self.colors["text_bright"], width=1)
    
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
    
    def draw_vram_bar(self, canvas, used, total):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        
        if w <= 1 or total <= 0:
            return
        
        pct = used / total
        fill_w = int(w * pct)
        
        # Gradient from purple to pink
        if fill_w > 0:
            for i in range(fill_w):
                ratio = i / w
                r = int(168 + (255 - 168) * ratio)
                g = int(85 + (107 - 85) * ratio)
                b = int(247 + (157 - 247) * ratio)
                color = f"#{r:02x}{g:02x}{b:02x}"
                canvas.create_line(i, 0, i, h, fill=color)
    
    # ==================== ANIMATIONS ====================
    
    def animate(self):
        """Main animation loop"""
        self.pulse_state = (self.pulse_state + 1) % 20
        self.alert_flash = not self.alert_flash
        
        # Scan line in header
        self.scan_line_pos = (self.scan_line_pos + 3) % (self.header_canvas.winfo_width() + 100)
        self.header_canvas.delete("scanline")
        self.header_canvas.create_line(
            self.scan_line_pos - 50, 0, self.scan_line_pos, 75,
            fill=self.colors["accent_cyan"], width=1, stipple="gray50", tags="scanline"
        )
        
        # Pulse status dot
        if self.is_critical and self.alert_flash:
            self.status_dot.config(fg=self.colors["critical"])
            self.status_text.config(fg=self.colors["critical"])
        elif self.is_critical:
            self.status_dot.config(fg=self.colors["bg_panel"])
        else:
            pulse = abs(10 - self.pulse_state) / 10
            if pulse > 0.5:
                self.status_dot.config(fg=self.colors["nominal"])
            else:
                self.status_dot.config(fg=self.colors["glow_green"])
        
        self.root.after(50, self.animate)
    
    # ==================== UI UPDATES ====================
    
    def update_gpu(self):
        t1, t2 = self.get_gpu_temps()
        
        # Check for critical state
        self.is_critical = False
        
        if t1 is not None:
            self.current_gpu_temp = t1
            self.draw_gauge(self.gpu_temp_canvas, t1, 100, label="°C")
            c, s = self.get_temp_color_status(t1, (55, 80))
            self.gpu_temp_status.config(text=s, fg=c)
            self.gpu_temp_history.pop(0)
            self.gpu_temp_history.append(t1)
            if t1 > 80:
                self.is_critical = True
        else:
            self.draw_gauge(self.gpu_temp_canvas, 0, 100, label="°C")
            self.gpu_temp_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
        if t2 is not None:
            self.draw_gauge(self.gpu_hotspot_canvas, t2, 100, label="°C")
            c, s = self.get_temp_color_status(t2, (60, 85))
            self.gpu_hotspot_status.config(text=s, fg=c)
            if t2 > 85:
                self.is_critical = True
        else:
            self.draw_gauge(self.gpu_hotspot_canvas, 0, 100, label="°C")
            self.gpu_hotspot_status.config(text="● NO ACCESS", fg=self.colors["text_dim"])
        
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
            self.vram_label.config(text=f"{used_gb:.1f} / {total_gb:.0f} GB")
            self.draw_vram_bar(self.vram_canvas, used, total)
        
        # Fans
        rpm = self.get_gpu_fans()
        self.fan_label.config(text=f"{rpm} RPM")
        if rpm > 0:
            self.fan_status.config(text="● ACTIVE", fg=self.colors["accent_teal"])
        else:
            self.fan_status.config(text="● IDLE", fg=self.colors["text_dim"])
        
        # Graph
        color = self.colors["critical"] if self.is_critical else self.colors["accent_blue"]
        self.draw_graph(self.gpu_graph_canvas, self.gpu_temp_history, color, 100)
    
    def update_cpu(self):
        usage = self.get_cpu_usage()
        temp = self.get_cpu_temp()
        nvme = self.get_nvme_temp()
        freq = self.get_cpu_freq()
        cores, threads = self.get_cpu_info()
        
        self.cpu_history.pop(0)
        self.cpu_history.append(usage)
        self.current_cpu_usage = usage
        
        # Usage gauge
        self.draw_gauge(self.cpu_usage_canvas, usage, 100, label="%")
        
        # Temp gauge
        if temp is not None:
            self.current_cpu_temp = temp
            self.draw_gauge(self.cpu_temp_canvas, temp, 100, label="°C")
            c, s = self.get_temp_color_status(temp, (55, 75))
            self.cpu_temp_status.config(text=s, fg=c)
            if temp > 75:
                self.is_critical = True
        
        # NVMe
        if nvme is not None:
            c, _ = self.get_temp_color_status(nvme, (50, 70))
            self.nvme_temp_label.config(text=f"{nvme:.0f}°C", fg=c)
        
        self.cpu_freq_label.config(text=f"{freq} MHz")
        self.cpu_cores_label.config(text=f"{cores}C / {threads}T")
        
        # Graph
        color = self.colors["critical"] if usage > 80 else self.colors["warning"] if usage > 50 else self.colors["accent_green"]
        self.draw_graph(self.cpu_graph_canvas, self.cpu_history, color)
    
    def update_cpu_cores(self):
        usages = self.get_per_core_usage()
        
        for i, usage in enumerate(usages):
            if i < len(self.core_canvases):
                self.draw_gradient_bar(self.core_canvases[i], usage)
                
                if usage > 80:
                    color = self.colors["critical"]
                elif usage > 50:
                    color = self.colors["warning"]
                else:
                    color = self.colors["accent_green"]
                
                self.core_labels[i].config(text=f"{usage:.0f}%", fg=color)
    
    def update_memory(self):
        mem = self.get_memory_info()
        if mem:
            self.ram_percent.config(text=f"{mem['mem_percent']:.1f}%")
            self.ram_details.config(text=f"{self.format_bytes(mem['mem_used'])} / {self.format_bytes(mem['mem_total'])}")
            self.draw_gradient_bar(self.ram_canvas, mem['mem_percent'])
            
            self.swap_percent.config(text=f"{mem['swap_percent']:.1f}%")
            self.swap_details.config(text=f"{self.format_bytes(mem['swap_used'])} / {self.format_bytes(mem['swap_total'])}")
            self.draw_gradient_bar(self.swap_canvas, mem['swap_percent'])
    
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
            
            bar_canvas = tk.Canvas(row, height=10, width=60, bg=self.colors["bg_card"], highlightthickness=0)
            bar_canvas.pack(side="right", padx=3)
            self.draw_gradient_bar(bar_canvas, pct)
    
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
        
        # Update status text based on critical state
        if self.is_critical:
            self.status_text.config(text="⚠ THERMAL WARNING", fg=self.colors["critical"])
        else:
            self.status_text.config(text="ALL SYSTEMS NOMINAL", fg=self.colors["nominal"])
    
    def update_time(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%A, %B %d, %Y"))
    
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
        print("  ⚡ SYSTEM COMMAND CENTER v4 - Eye Candy Edition")
        print("  Run with sudo for GPU temperature monitoring:")
        print("  sudo python3 system_command_center_v4.py")
        print("  ")
        print("  Press F11 for fullscreen mode")
        print("=" * 60)
        print()
    
    root = tk.Tk()
    app = SystemCommandCenter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
