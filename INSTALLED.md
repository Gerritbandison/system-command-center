# ✅ System Command Center - Installation Summary

**Date:** February 6, 2026  
**Version:** v4.0 (Eye Candy Edition)  
**Installation Type:** Local User Install

---

## 📂 What Was Installed

### Executable Files
- **Main Monitor:** `~/.local/bin/sysmon` (55 KB)
- **Sudo Wrapper:** `~/.local/bin/sysmon-sudo` (convenience script)

### Desktop Integration
- **Desktop Entry:** `~/.local/share/applications/sysmon.desktop`
- **Menu Name:** "System Command Center"
- **Categories:** System > Monitor > Utility

### Installation Scripts
- `install.sh` - System-wide installer (requires sudo)
- `install-local.sh` - User-space installer (no sudo needed)

---

## 🚀 How to Launch

### Option 1: Terminal (with GPU temps)
```bash
sysmon-sudo
```

### Option 2: Terminal (without GPU temps)
```bash
sysmon
```

### Option 3: Application Menu
1. Open your application launcher (Super key)
2. Search for **"System Command Center"**
3. Click to launch (will prompt for password for GPU access)

---

## 🎯 Features Available

### Real-Time Monitoring
✅ **Intel Arc B580 GPU**
- Temperature (via Intel PMT telemetry)
- Hotspot temperature
- GPU clock frequency
- VRAM usage
- Fan RPM (3 fans)

✅ **AMD Ryzen CPU**
- Temperature (via k10temp)
- Per-core utilization
- Total CPU usage
- Clock frequency

✅ **System Sensors**
- NVMe SSD temperature
- Network I/O (RX/TX graphs)
- Disk I/O (read/write speeds)
- RAM + Swap usage
- Storage device usage
- WiFi signal strength
- Top processes by CPU

### Visual Features (v4)
- 🎨 Animated circular gauges with glow effects
- 📊 Color gradient progress bars (green → yellow → red)
- ⚠️ Pulsing critical temperature alerts
- 📺 Fullscreen mode (**Press F11**)
- ⚡ Scan line animation in header
- 🎭 Smooth animations and transitions

---

## 🔐 Permissions

**GPU Temperature Access Requires Root**

Your Intel Arc B580 temps are read from:
```
/sys/class/intel_pmt/telem2/telem
```

This file is **root-only readable**. That's why you need sudo.

**Without sudo:**
- CPU temps ✅ Work
- GPU temps ❌ Show "NO ACCESS"
- All other features ✅ Work

**With sudo:**
- Everything works ✅

---

## 🛠️ Troubleshooting

### "sysmon: command not found"
Your PATH is fine since the installer verified it. Try:
```bash
source ~/.bashrc
```

### "GPU temps show NO ACCESS"
Run with sudo:
```bash
sysmon-sudo
```

### "TclError: no display"
You're running it over SSH or without a display server. 
Run it on your actual desktop with a GUI.

### Desktop launcher doesn't appear
Update the desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

---

## 📊 Your Hardware Profile

Based on your sensors output:

| Component | Sensor | Current Temp |
|-----------|--------|--------------|
| **CPU** | k10temp (Tctl) | 48.9°C |
| **GPU** | xe-pci (pkg) | 53.0°C |
| **GPU VRAM** | xe-pci (vram) | 60.0°C |
| **NVMe SSD** | nvme-pci | 45.9°C |
| **GPU Fans** | 3x detected (idle: 0 RPM) |

Your system is running cool. GPU fans at 0 RPM means passive cooling is handling the load.

---

## 🎮 Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **F11** | Toggle fullscreen mode |
| **Escape** | Exit fullscreen |
| **Ctrl+C** | Quit (in terminal) |

---

## 📝 Configuration

### Temperature Thresholds

Edit these in `system_command_center_v4.py` to customize alert levels:

```python
# Line ~570-580 (approximate)
self.get_temp_color_status(temp, (55, 75))  # CPU: warning at 75°C
self.get_temp_color_status(temp, (55, 80))  # GPU: warning at 80°C
self.get_temp_color_status(temp, (60, 85))  # Hotspot: warning at 85°C
```

### Update Interval

Default: 1 second  
To change, modify line ~1100:
```python
self.root.after(1000, self.update_all)  # 1000ms = 1 second
```

---

## 🔄 Uninstall

To remove the installation:

```bash
# Remove executables
rm ~/.local/bin/sysmon ~/.local/bin/sysmon-sudo

# Remove desktop entry
rm ~/.local/share/applications/sysmon.desktop

# Remove the source folder (optional)
rm -rf ~/system-command-center
```

---

## 🌐 GitHub Repository

**URL:** https://github.com/Gerritbandison/system-command-center

**Latest commits:**
- `be50dab` - Update README with new installation instructions
- `3b1321c` - Add installation scripts (system-wide and local user installs)
- `2f37ddb` - Initial commit: System Command Center v1-v4

---

## 📈 Next Steps

### Immediate
- [x] Install the monitor
- [ ] Launch `sysmon-sudo` to test
- [ ] Press F11 for fullscreen mode
- [ ] Monitor temps during a stress test

### Future Enhancements
- [ ] Add data logging to CSV
- [ ] Add desktop notifications for critical temps
- [ ] Add multi-GPU support (NVIDIA, AMD)
- [ ] Create web dashboard version
- [ ] Add overclocking profiles

---

## 💡 Pro Tips

1. **Launch at startup:** Add `sysmon` to your Startup Applications
2. **Second monitor:** Run in fullscreen on a secondary display
3. **Gaming overlay:** Use as a side panel while gaming
4. **Benchmarking:** Monitor temps during stress tests
5. **Share stats:** Take screenshots with F11 fullscreen

---

**Enjoy your new system monitor!** 🎉

If you run into any issues, check the GitHub issues page or create a new one.
