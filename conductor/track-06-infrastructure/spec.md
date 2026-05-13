# Track 06: Infrastructure & Security - Specification

## Objective
Secure the application by placing it behind an Nginx reverse proxy, enabling SSL, and restricting direct access to the application port.

## Requirements
1. **Nginx Reverse Proxy:** Install and configure Nginx to proxy requests to the FastAPI application running on port 8000.
2. **SSL/HTTPS:** Use Certbot (Let's Encrypt) to obtain and configure SSL certificates. Redirect all HTTP traffic to HTTPS.
3. **Firewall:** Configure UFW (Uncomplicated Firewall) to allow SSH, HTTP (80), and HTTPS (443), while blocking external access to port 8000.

## Deliverables
- Nginx configuration file (e.g., `/etc/nginx/sites-available/tascam`).
- Instructions/scripts for setting up Certbot and UFW.
