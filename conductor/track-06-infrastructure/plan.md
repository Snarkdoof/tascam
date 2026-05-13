# Track 06: Infrastructure & Security - Plan

## Step 1: Nginx Configuration
- Create a template Nginx configuration file that sets up a `server` block listening on port 80.
- Configure `location /` to `proxy_pass` to `http://127.0.0.1:8000`.
- Ensure proper proxy headers are set (`Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`).

## Step 2: SSL Setup (Certbot)
- Document the commands required to install Certbot and the Nginx plugin.
- Document the command to obtain and install the certificate (`certbot --nginx -d <domain>`).

## Step 3: Firewall Configuration (UFW)
- Document the commands to configure UFW:
  - `ufw allow OpenSSH`
  - `ufw allow 'Nginx Full'`
  - `ufw deny 8000`
  - `ufw enable`

## Step 4: Verification
- Verify that accessing the server via HTTP redirects to HTTPS.
- Verify that the application is accessible via HTTPS.
- Verify that accessing port 8000 directly from outside the server times out or is rejected.
