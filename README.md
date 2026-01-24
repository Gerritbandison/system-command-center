# ⚡ System Command Center

A comprehensive system monitoring dashboard for Linux systems, specifically optimized for **Intel Arc B580** GPUs and **AMD Ryzen** CPUs.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Linux-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### Hardware Monitoring
- **Intel Arc B580 GPU**
  - Temperature via Intel PMT telemetry (requires sudo)
  - Hotspot temperature
  - GPU clock frequency
  - VRAM usage
  - Fan RPM
- **AMD Ryzen CPU**
  - Temperature via k10temp
  - Per-core utilization
  - Total utilization
  - Clock frequency
- **NVMe SSD** temperature
- **Network I/O** with live graphs
- **Disk I/O** read/write speeds
- **Memory** (RAM + Swap)
- **Storage** device usage
- **WiFi** signal strength
- **Top processes** by CPU usage

### Visual Features (v4)
- Animated circular gauges with glow effects
- Color gradient progress bars (green → yellow → red)
- Pulsing status indicator
- Critical temperature alerts with flashing warnings
- Scan line animation in header
- Fullscreen mode (F11)

## Versions

| Version | Description |
|---------|-------------|
| `temp_monitor.py` | Simple dual-panel temp monitor (CPU + GPU) |
| `system_command_center.py` | v1 - Basic full dashboard |
| `system_command_center_v2.py` | v2 - Added GPU temps via Intel PMT telemetry |
| `system_command_center_v3.py` | v3 - Added NVMe temp, per-core CPU, VRAM, fans, WiFi, disk I/O |
| `system_command_center_v4.py` | v4 - Eye candy: gauges, gradients, animations, fullscreen |

## Requirements

### System Requirements
- Linux (tested on Linux Mint, Ubuntu)
- Python 3.8+
- Intel Arc B580 GPU with Xe driver (kernel 6.12+)
- AMD Ryzen CPU

### Python Dependencies
```bash
# tkinter (usually included with Python)
sudo apt install python3-tk

# lm-sensors for temperature monitoring
sudo apt install lm-sensors
sudo sensors-detect
```

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/system-command-center.git
cd system-command-center

# Install dependencies
sudo apt install python3-tk lm-sensors

# Run the latest version (v4)
sudo python3 system_command_center_v4.py
```

## Usage

```bash
# Run with sudo for GPU temperature access
sudo python3 system_command_center_v4.py

# Or run without sudo (GPU temps will show "NO ACCESS")
python3 system_command_center_v4.py
```

### Keyboard Shortcuts
- **F11** - Toggle fullscreen mode
- **Escape** - Exit fullscreen

## Screenshots

*Add your screenshots here*

## GPU Temperature Discovery

The Intel Arc B580 uses the Xe driver which doesn't expose temperature through standard hwmon. This project reads GPU temps directly from Intel's Platform Monitoring Technology (PMT) telemetry interface:

```
/sys/class/intel_pmt/telem2/telem
```

Temperature values are found at:
- Offset `0xa4`: GPU temperature
- Offset `0xa8`: Hotspot temperature

## File Paths Used

| Data | Path |
|------|------|
| CPU temp | `/sys/class/hwmon/hwmon2/temp1_input` (k10temp) |
| GPU temp | `/sys/class/intel_pmt/telem2/telem` (PMT telemetry) |
| GPU freq | `/sys/class/drm/card1/device/tile0/gt0/freq0/act_freq` |
| GPU VRAM | `/sys/class/drm/card1/device/mem_info_vram_*` |
| GPU fans | `/sys/class/hwmon/hwmon3/fan*_input` |
| NVMe temp | `/sys/class/hwmon/hwmon1/temp1_input` |
| Network | `/sys/class/net/*/statistics/*_bytes` |
| Disk I/O | `/proc/diskstats` |

> **Note:** hwmon numbers may vary on your system. Check with `sensors` command.

## Customization

### Temperature Thresholds
Edit the threshold tuples in `get_temp_color_status()`:
```python
# (nominal_max, warning_max) - above warning_max is critical
self.get_temp_color_status(temp, (55, 75))  # CPU
self.get_temp_color_status(temp, (55, 80))  # GPU
self.get_temp_color_status(temp, (60, 85))  # Hotspot
```

### Colors
Modify the `self.colors` dictionary to change the color scheme.

### Refresh Rate
Change the update interval (in milliseconds):
```python
self.root.after(1000, self.update_all)  # 1000ms = 1 second
```

## Troubleshooting

### GPU temps show "NO ACCESS"
- Run with `sudo`
- Check if Intel PMT is available: `ls /sys/class/intel_pmt/`

### Wrong hwmon numbers
```bash
# Find correct hwmon for each sensor
for h in /sys/class/hwmon/hwmon*; do echo "=== $h ==="; cat "$h/name" 2>/dev/null; done
```

### No GPU frequency
- Ensure Xe driver is loaded: `lsmod | grep xe`
- Check kernel version: `uname -r` (need 6.12+ for Battlemage)

## Contributing

Contributions are welcome! Feel free to:
- Add support for other GPUs (NVIDIA, AMD)
- Add new monitoring features
- Improve the UI
- Fix bugs

## License

MIT License - feel free to use, modify, and distribute.

## Acknowledgments

- Intel for the PMT telemetry interface
- The Linux kernel Xe driver developers
- Claude AI for pair programming assistance
