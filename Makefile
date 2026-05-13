# Deployment Config
SERVER_IP ?= 134.98.147.52
SSH_USER ?= ubuntu
SSH_KEY ?= $(HOME)/.ssh/id_rsa
REMOTE_PATH ?= /home/$(SSH_USER)/tascam

.PHONY: run import export deploy remote-install remote-run

run:
	uv run uvicorn tascam_app.web:app --host 0.0.0.0 --reload

import:
ifdef DIR
	uv run python process.py import-dir "$(DIR)" $(if $(OVERWRITE),--overwrite,)
else
	uv run python process.py import-dir $(if $(OVERWRITE),--overwrite,)
endif

export:
	uv run python process.py export

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

deploy-data:
	@echo "--- Syncing Database and Clips to $(SERVER_IP) ---"
	rsync -avz --progress \
		-e "ssh -i $(SSH_KEY)" \
		tascam.db $(SSH_USER)@$(SERVER_IP):$(REMOTE_PATH)/
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
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "cd $(REMOTE_PATH) && nohup /home/$(SSH_USER)/.local/bin/uv run uvicorn tascam_app.web:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &"
	@echo "--- App started in background. Logs are in app.log ---"
