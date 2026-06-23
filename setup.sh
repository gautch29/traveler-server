#!/bin/bash

# Exit on error
set -e

# Colors
GREEN='\033[0;32m'
NC='\033[0m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'

echo -e "${BLUE}=== Traveler Server - Debian Systemd Setup ===${NC}"

# Check root permissions
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}Please run as root (or using sudo) to create systemd service.${NC}"
  exit 1
fi

# Detect directory of setup script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Prompt for port only
read -p "Enter Port [8000]: " PORT
PORT=${PORT:-8000}

# Create systemd service
SERVICE_PATH="/etc/systemd/system/traveler-server.service"

echo -e "${BLUE}Creating systemd service file at $SERVICE_PATH...${NC}"

cat <<EOF > "$SERVICE_PATH"
[Unit]
Description=Traveler Mock Server Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$DIR
ExecStart=/usr/bin/python3 -u mock_server.py --port $PORT
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Reload and restart
echo -e "${BLUE}Reloading systemd daemon...${NC}"
systemctl daemon-reload

echo -e "${BLUE}Enabling traveler-server service on boot...${NC}"
systemctl enable traveler-server.service

echo -e "${BLUE}Starting traveler-server service...${NC}"
systemctl restart traveler-server.service

echo -e "${GREEN}=== Setup Succeeded! ===${NC}"
echo -e "Traveler Mock Server is now running on HTTP port $PORT."
echo -e "Service status details:"
systemctl status traveler-server.service --no-pager
