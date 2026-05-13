#!/bin/bash
set -e

echo "--- Installing Nginx & Certbot ---"
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "--- Configuring Nginx ---"
sudo cp /home/ubuntu/tascam/tascam_nginx.conf /etc/nginx/sites-available/tascam
sudo ln -sf /etc/nginx/sites-available/tascam /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "--- Generating SSL Certificates ---"
# We run certbot non-interactively. It will automatically reconfigure Nginx to redirect HTTP to HTTPS.
sudo certbot --nginx -d bbb.njaal.net -d music.njaal.net --non-interactive --agree-tos -m njaal@njaal.net --redirect

echo "--- Securing Firewall (Blocking 8000 externally) ---"
# Remove the direct 8000 port access if it exists
sudo iptables -D INPUT -p tcp --dport 8000 -j ACCEPT 2>/dev/null || true
# Ensure 80 and 443 are allowed
sudo iptables -I INPUT 6 -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
sudo iptables -I INPUT 6 -p tcp --dport 443 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save

echo "--- Infrastructure Setup Complete! ---"
