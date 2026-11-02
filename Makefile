# Deployment Config
SERVER_IP ?= 134.98.147.52
SSH_USER ?= ubuntu
SSH_KEY ?= $(HOME)/.ssh/id_rsa
REMOTE_PATH ?= /home/$(SSH_USER)/tascam

.PHONY: run import export deploy remote-install remote-run

run:
	uv run uvicorn tascam_app.web:app --host 0.0.0.0 --reload

import:
	@echo "--- Opening SSH Tunnel to Postgres (Port 5432) ---"
	ssh -f -N -L 5432:localhost:5432 -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP)
	@echo "--- Tunnel Opened. Running Local Import against Remote DB ---"
	DATABASE_URL="postgresql://tascam_user:tascam_secure_pass_123@localhost:5432/tascam_db" uv run python process.py import-dir $(if $(DIR),"$(DIR)",) $(if $(OVERWRITE),--overwrite,) || true
	@echo "--- Closing SSH Tunnel ---"
	pkill -f "[s]sh -f -N -L 5432:localhost:5432" || true
	@$(MAKE) deploy-data

export:
	DATABASE_URL="postgresql://tascam_user:tascam_secure_pass_123@localhost:5432/tascam_db" uv run python process.py export

deploy:
	@echo "--- Deploying Code to $(SERVER_IP) ---"
	rsync -avz --progress \
		--exclude '.git/' \
		--exclude '__pycache__/' \
		--exclude '.venv/' \
		--exclude 'data/' \
		--exclude 'exports/' \
		--exclude 'tmp*/' \
		--exclude '*.db*' \
		--exclude '*.log' \
		-e "ssh -i $(SSH_KEY)" \
		./ $(SSH_USER)@$(SERVER_IP):$(REMOTE_PATH)
	@echo "--- Code Deployment Complete ---"

remote-db-setup: deploy
	@echo "--- 🚨 WARNING: THIS WILL DESTROY ALL DATA IN THE REMOTE POSTGRES DB 🚨 ---"
	@echo "--- It will recreate the schema and import data from the local SQLite file ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "bash $(REMOTE_PATH)/setup-pg.sh"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "cd $(REMOTE_PATH) && /home/$(SSH_USER)/.local/bin/uv run python migrate_db.py"
	@echo "--- Database Migration Complete! ---"

deploy-data:
	@echo "--- Syncing Clips to $(SERVER_IP) ---"
	rsync -avz --progress \
		-e "ssh -i $(SSH_KEY)" \
		data/clips/ $(SSH_USER)@$(SERVER_IP):$(REMOTE_PATH)/data/clips/
	@echo "--- Data Sync Complete ---"

remote-install:
	@echo "--- Running installation script on remote ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "bash $(REMOTE_PATH)/install-ubuntu.sh"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "cd $(REMOTE_PATH) && /home/$(SSH_USER)/.local/bin/uv sync"

remote-infra:
	@echo "--- Setting up Nginx, SSL, and Firewall on remote ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "bash $(REMOTE_PATH)/setup-infra.sh"

remote-run:
	@echo "--- Starting app on remote ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "cd $(REMOTE_PATH) && nohup /home/$(SSH_USER)/.local/bin/uv run uvicorn tascam_app.web:app --host 0.0.0.0 --port 8000 > app.log 2>&1 < /dev/null &"
	@echo "--- App started in background. Logs are in app.log ---"

remote-restart:
	@echo "--- Restarting app on remote ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "pkill -f 'uvicorn tascam_app.web:app' || true"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "cd $(REMOTE_PATH) && nohup /home/$(SSH_USER)/.local/bin/uv run uvicorn tascam_app.web:app --host 0.0.0.0 --port 8000 > app.log 2>&1 < /dev/null &"
	@echo "--- App restarted in background. Logs are in app.log ---"
