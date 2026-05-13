#!/bin/bash
set -e

echo "--- Updating System ---"
sudo apt-get update
sudo apt-get upgrade -y

echo "--- Installing Dependencies (FFmpeg, Python, etc.) ---"
sudo apt-get install -y ffmpeg python3-pip python3-venv curl iptables-persistent netfilter-persistent

echo "--- Installing 'uv' ---"
curl -LsSf https://astral.sh/uv/install.sh | sh
# Ensure uv is in the path for the rest of this script
export PATH="$HOME/.cargo/bin:$PATH"

echo "--- Configuring Firewall (Ports 80, 443, 8000) ---"
# Insert rules at the top of the INPUT chain to ensure they override defaults
sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save

echo "--- Setup Complete! ---"
echo "You can now run 'uv sync' in the project directory to install Python dependencies."
