#!/bin/bash
# System Command Center Installer (User Mode)
# Installs to ~/.local/bin (no sudo required for installation)

set -e

echo "========================================================"
echo "  ⚡ System Command Center v4 Installer"
echo "========================================================"
echo ""

# Check dependencies
echo "📦 Checking dependencies..."

if ! command -v sensors &> /dev/null; then
    echo "⚠️  lm-sensors not found"
    echo "   Run: sudo apt install lm-sensors python3-tk"
    echo "   Then run: sudo sensors-detect --auto"
    read -p "   Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update && sudo apt install -y lm-sensors python3-tk
        sudo sensors-detect --auto
    fi
else
    echo "✅ lm-sensors already installed"
fi

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "⚠️  python3-tk not found"
    read -p "   Install now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt install -y python3-tk
    fi
else
    echo "✅ python3-tk already installed"
fi

# Install to user's local bin
echo ""
echo "📋 Installing system monitor..."
mkdir -p ~/.local/bin
cp system_command_center_v4.py ~/.local/bin/sysmon
chmod +x ~/.local/bin/sysmon

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "⚠️  ~/.local/bin is not in your PATH"
    echo "   Add this to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# Create desktop entry
echo "🖥️  Creating desktop launcher..."
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/sysmon.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=System Command Center
Comment=Real-time hardware monitoring for Intel Arc + AMD Ryzen
Exec=pkexec /home/$USER/.local/bin/sysmon
Icon=utilities-system-monitor
Terminal=false
Categories=System;Monitor;Utility;
Keywords=monitor;hardware;gpu;cpu;temperature;arc;
EOF

# Replace $USER with actual username
sed -i "s/\$USER/$USER/g" ~/.local/share/applications/sysmon.desktop

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications 2>/dev/null || true
fi

# Create wrapper script for easy sudo access
cat > ~/.local/bin/sysmon-sudo << 'EOF'
#!/bin/bash
sudo ~/.local/bin/sysmon "$@"
EOF
chmod +x ~/.local/bin/sysmon-sudo

echo ""
echo "========================================================"
echo "  ✅ Installation Complete!"
echo "========================================================"
echo ""
echo "📍 Installed to: ~/.local/bin/sysmon"
echo ""
echo "🚀 Run the monitor:"
echo "   1. With GPU access: sysmon-sudo"
echo "   2. Without sudo:    sysmon"
echo "   3. From app menu:   Search for 'System Command Center'"
echo ""
echo "💡 Tips:"
echo "   - Press F11 for fullscreen mode"
echo "   - GPU temperatures require sudo (use sysmon-sudo)"
echo "   - Arc B580 temps read from Intel PMT telemetry"
echo ""
echo "📝 Next steps:"
echo "   - Run: sysmon-sudo"
echo "   - Or launch from your application menu"
echo ""
