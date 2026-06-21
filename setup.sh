#!/bin/bash

# Exit on error
set -e

# Colors for pretty outputs
GREEN='\033[0;32m'
NC='\033[0m' # No Color
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

# Prompts
read -p "Enter Port [8000]: " PORT
PORT=${PORT:-8000}

read -p "Enter Server Access Token [traveler_secret_token_2026]: " TOKEN
TOKEN=${TOKEN:-traveler_secret_token_2026}

read -p "Run behind reverse proxy (use plain HTTP locally)? (y/n) [y]: " REVERSE_PROXY
REVERSE_PROXY=${REVERSE_PROXY:-y}

# Build parameters
EXEC_ARGS="--port $PORT --token $TOKEN"
if [ "$REVERSE_PROXY" = "y" ] || [ "$REVERSE_PROXY" = "yes" ]; then
  EXEC_ARGS="$EXEC_ARGS --http"
fi

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
ExecStart=/usr/bin/python3 -u mock_server.py $EXEC_ARGS
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
echo -e "Traveler service status:"
systemctl status traveler-server.service --no-pager

echo ""
echo -e "${YELLOW}=== Reverse Proxy Configuration Guide ===${NC}"
if [ "$REVERSE_PROXY" = "y" ] || [ "$REVERSE_PROXY" = "yes" ]; then
  echo "Because you selected HTTP mode (running behind reverse proxy):"
  echo "The python server is listening on: http://localhost:$PORT"
  echo ""
  echo "Here is a sample Nginx reverse proxy configuration block:"
  echo "--------------------------------------------------------"
  echo "server {"
  echo "    server_name yourdomain.com;"
  echo ""
  echo "    location / {"
  echo "        proxy_pass http://127.0.0.1:$PORT;"
  echo "        proxy_set_header Host \$host;"
  echo "        proxy_set_header X-Real-IP \$remote_addr;"
  echo "        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
  echo "        proxy_set_header X-Forwarded-Proto \$scheme;"
  echo "        client_max_body_size 200M;" # Allow uploading modified configs
  echo "    }"
  echo ""
  echo "    listen 80;"
  echo "}"
  echo "--------------------------------------------------------"
  echo "Make sure to run certbot (Let's Encrypt) to secure the domain with SSL!"
else
  echo "The server is running directly in HTTPS mode on port $PORT."
  echo "It generated self-signed certificates 'server.crt' and 'server.key'."
fi
