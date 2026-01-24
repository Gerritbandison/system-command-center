#!/usr/bin/env python3
"""
Temperature Monitor for Intel Arc B580 and AMD Ryzen
A simple GUI to display GPU and CPU temperatures in real-time.
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import re
import os
from pathlib import Path


class TemperatureMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("System Temperature Monitor")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)
        
        # Style configuration
        self.colors = {
            "bg": "#1a1a2e",
            "card_bg": "#16213e",
            "accent_blue": "#0f9fff",
            "accent_orange": "#ff6b35",
            "text": "#eaeaea",
            "text_dim": "#8892a0",
            "cool": "#00d4aa",
            "warm": "#ffc107",
            "hot": "#ff4757"
        }
        
        self.setup_ui()
        self.update_temperatures()
    
    def setup_ui(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg=self.colors["bg"], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title = tk.Label(
            main_frame,
            text="🌡️ TEMPERATURE MONITOR",
            font=("Monospace", 14, "bold"),
            fg=self.colors["text"],
            bg=self.colors["bg"]
        )
        title.pack(pady=(0, 20))
        
        # Cards container
        cards_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        cards_frame.pack(fill="both", expand=True)
        
        # GPU Card
        self.gpu_card = self.create_card(
            cards_frame,
            "INTEL ARC B580",
            "GPU",
            self.colors["accent_blue"]
        )
        self.gpu_card.pack(side="left", padx=(0, 10), fill="both", expand=True)
        
        # CPU Card
        self.cpu_card = self.create_card(
            cards_frame,
            "AMD RYZEN 7",
            "CPU",
            self.colors["accent_orange"]
        )
        self.cpu_card.pack(side="left", padx=(10, 0), fill="both", expand=True)
        
        # Status bar
        self.status_label = tk.Label(
            main_frame,
            text="Updating every 2 seconds...",
            font=("Monospace", 9),
            fg=self.colors["text_dim"],
            bg=self.colors["bg"]
        )
        self.status_label.pack(pady=(15, 0))
    
    def create_card(self, parent, title, device_type, accent_color):
        card = tk.Frame(parent, bg=self.colors["card_bg"], padx=25, pady=20)
        
        # Accent bar at top
        accent_bar = tk.Frame(card, bg=accent_color, height=3)
        accent_bar.pack(fill="x", pady=(0, 15))
        
        # Device type label
        type_label = tk.Label(
            card,
            text=device_type,
            font=("Monospace", 10),
            fg=accent_color,
            bg=self.colors["card_bg"]
        )
        type_label.pack(anchor="w")
        
        # Title
        title_label = tk.Label(
            card,
            text=title,
            font=("Monospace", 11, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card_bg"]
        )
        title_label.pack(anchor="w", pady=(2, 15))
        
        # Temperature display
        temp_frame = tk.Frame(card, bg=self.colors["card_bg"])
        temp_frame.pack(anchor="w")
        
        temp_label = tk.Label(
            temp_frame,
            text="--",
            font=("Monospace", 42, "bold"),
            fg=self.colors["text"],
            bg=self.colors["card_bg"]
        )
        temp_label.pack(side="left")
        
        unit_label = tk.Label(
            temp_frame,
            text="°C",
            font=("Monospace", 18),
            fg=self.colors["text_dim"],
            bg=self.colors["card_bg"]
        )
        unit_label.pack(side="left", anchor="n", pady=(8, 0))
        
        # Status indicator
        status_label = tk.Label(
            card,
            text="● Reading...",
            font=("Monospace", 10),
            fg=self.colors["text_dim"],
            bg=self.colors["card_bg"]
        )
        status_label.pack(anchor="w", pady=(10, 0))
        
        # Store references
        card.temp_label = temp_label
        card.status_label = status_label
        card.accent_color = accent_color
        
        return card
    
    def get_gpu_temp(self):
        """Get Intel Arc GPU temperature from hwmon or sensors"""
        try:
            # Try hwmon3 (xe driver on this system)
            temp_file = Path("/sys/class/hwmon/hwmon3/temp1_input")
            if temp_file.exists():
                temp = int(temp_file.read_text().strip()) / 1000
                return temp
            
            # Fallback: parse sensors output
            result = subprocess.run(
                ["sensors"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Look for xe-pci section with temp
                in_xe_section = False
                for line in result.stdout.split('\n'):
                    if 'xe-pci' in line:
                        in_xe_section = True
                    elif in_xe_section and ':' in line and any(x in line.lower() for x in ['temp', 'junction', 'edge']):
                        match = re.search(r'([+-]?\d+\.?\d*)\s*°C', line)
                        if match:
                            return float(match.group(1))
                    elif in_xe_section and line.strip() == '':
                        in_xe_section = False
            
            return None
        except Exception as e:
            return None
    
    def get_cpu_temp(self):
        """Get AMD Ryzen CPU temperature from hwmon2 (k10temp)"""
        try:
            # Direct path to k10temp on this system
            temp_file = Path("/sys/class/hwmon/hwmon2/temp1_input")
            if temp_file.exists():
                temp = int(temp_file.read_text().strip()) / 1000
                return temp
            
            # Fallback: try sensors command
            result = subprocess.run(
                ["sensors"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Look for k10temp Tctl
                for line in result.stdout.split('\n'):
                    if 'Tctl:' in line or 'Tdie:' in line:
                        match = re.search(r'([+-]?\d+\.?\d*)\s*°C', line)
                        if match:
                            return float(match.group(1))
            
            return None
        except Exception as e:
            return None
    
    def get_temp_status(self, temp, is_gpu=False):
        """Get status text and color based on temperature"""
        if temp is None:
            return "● Not detected", self.colors["text_dim"]
        
        # Different thresholds for GPU vs CPU
        if is_gpu:
            if temp < 50:
                return "● Cool", self.colors["cool"]
            elif temp < 75:
                return "● Normal", self.colors["warm"]
            else:
                return "● Hot", self.colors["hot"]
        else:
            if temp < 55:
                return "● Cool", self.colors["cool"]
            elif temp < 75:
                return "● Normal", self.colors["warm"]
            else:
                return "● Hot", self.colors["hot"]
    
    def update_temperatures(self):
        """Update temperature readings"""
        # GPU
        gpu_temp = self.get_gpu_temp()
        if gpu_temp is not None:
            self.gpu_card.temp_label.config(text=f"{gpu_temp:.0f}")
            status_text, status_color = self.get_temp_status(gpu_temp, is_gpu=True)
            self.gpu_card.status_label.config(text=status_text, fg=status_color)
        else:
            self.gpu_card.temp_label.config(text="--")
            self.gpu_card.status_label.config(
                text="● No temp sensor exposed", 
                fg=self.colors["text_dim"]
            )
        
        # CPU
        cpu_temp = self.get_cpu_temp()
        if cpu_temp is not None:
            self.cpu_card.temp_label.config(text=f"{cpu_temp:.0f}")
            status_text, status_color = self.get_temp_status(cpu_temp, is_gpu=False)
            self.cpu_card.status_label.config(text=status_text, fg=status_color)
        else:
            self.cpu_card.temp_label.config(text="--")
            self.cpu_card.status_label.config(text="● Not detected", fg=self.colors["text_dim"])
        
        # Schedule next update (2 seconds)
        self.root.after(2000, self.update_temperatures)


def main():
    root = tk.Tk()
    
    # Set minimum size
    root.minsize(450, 280)
    
    # Center window on screen
    root.update_idletasks()
    width = 450
    height = 280
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    app = TemperatureMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
