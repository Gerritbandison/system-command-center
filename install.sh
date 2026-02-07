#!/bin/bash
# System Command Center Installer
# Installs the v4 monitoring dashboard

set -e

echo "========================================================"
echo "  ⚡ System Command Center v4 Installer"
echo "========================================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Don't run this installer with sudo"
    echo "   The installer will prompt for sudo when needed"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."

if ! command -v sensors &> /dev/null; then
    echo "📥 Installing lm-sensors..."
    sudo apt update
    sudo apt install -y lm-sensors python3-tk
    echo "🔧 Running sensors-detect..."
    sudo sensors-detect --auto
else
    echo "✅ lm-sensors already installed"
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "📥 Installing python3-tk..."
    sudo apt install -y python3-tk
else
    echo "✅ python3-tk already installed"
fi

# Copy executable to /usr/local/bin
echo ""
echo "📋 Installing system monitor..."
sudo cp system_command_center_v4.py /usr/local/bin/sysmon
sudo chmod +x /usr/local/bin/sysmon

# Create desktop entry
echo "🖥️  Creating desktop launcher..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/sysmon.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=System Command Center
Comment=Real-time hardware monitoring for Intel Arc + AMD Ryzen
Exec=pkexec /usr/local/bin/sysmon
Icon=utilities-system-monitor
Terminal=false
Categories=System;Monitor;Utility;
Keywords=monitor;hardware;gpu;cpu;temperature;arc;
EOF

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

echo ""
echo "========================================================"
echo "  ✅ Installation Complete!"
echo "========================================================"
echo ""
echo "📍 Installed to: /usr/local/bin/sysmon"
echo ""
echo "🚀 Run the monitor:"
echo "   1. From terminal: sudo sysmon"
echo "   2. From app menu: Search for 'System Command Center'"
echo ""
echo "💡 Tips:"
echo "   - Press F11 for fullscreen mode"
echo "   - Run with sudo for GPU temperature access"
echo "   - Arc B580 temps require sudo"
echo ""
echo "🔗 GitHub: https://github.com/Gerritbandison/system-command-center"
echo ""
