.PHONY: run import

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
