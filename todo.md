# Todo list

This file tracks tasks planned for future implementation in the Tascam Audio Processor project.

- [ ] **Track 05: Cloud Backup**
  - Implement Google Cloud / Google Drive upload logic for original audio files.
  - Requires Google API credentials and setup.
- [ ] **Track 06: Infrastructure & Security**
  - Set up Nginx reverse proxy using [tascam_nginx.conf](file:///home/njaal/git/tascam/tascam_nginx.conf) on the server.
  - Configure SSL certificates using Certbot.
  - Configure UFW firewall to block port 8000 externally while allowing ports 80 and 443.
- [ ] **Track 07: Authentication & ACL**
  - Integrate Google Login and user accounts.
  - Complete backend verification and role enforcement (e.g., admin approvals).
