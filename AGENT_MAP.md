# Agent Map: Tascam Audio Processor

## A. System Architecture
This project is a Tascam audio processing and playback application. The backend is built using FastAPI with SQLModel/SQLAlchemy, supporting SQLite locally and PostgreSQL in production. The frontend is a static web interface utilizing Vanilla HTML, CSS, JavaScript, and MCorp/TimingSRC for synchronized media playback. Authentication is managed through Google OAuth and session-based access control.

## B. Core Directory Index
* `tascam_app`: Main application directory containing the FastAPI backend models, database session generators, templates, and web routes.
* `tascam_app/templates`: Jinja2 HTML templates for login, admin, and player interfaces.
* `conductor`: Track registry, product vision, plans, and specifications for development.
* `mock_tascam`: Simulated structure of a Tascam recorder's SD card directory for ingestion testing.

## C. Key Data/Type Routes
* `User Schema` -> [tascam_app/models.py](file:///home/njaal/git/tascam/tascam_app/models.py)
* `SourceFile Schema` -> [tascam_app/models.py](file:///home/njaal/git/tascam/tascam_app/models.py)
* `Song Schema` -> [tascam_app/models.py](file:///home/njaal/git/tascam/tascam_app/models.py)
* `Clip Schema` -> [tascam_app/models.py](file:///home/njaal/git/tascam/tascam_app/models.py)
* `Repertoire & RepertoireItem Schema` -> [tascam_app/models.py](file:///home/njaal/git/tascam/tascam_app/models.py)

## D. Data Flow / Request Lifecycle
1. **User Request**: User opens app (default start screen: Repertoire) or switches to Songs / Library -> Frontend JavaScript ([app.js](file:///home/njaal/git/tascam/tascam_app/static/app.js))
2. **API Routes**: HTTP requests are processed by FastAPI endpoints ([web.py](file:///home/njaal/git/tascam/tascam_app/web.py))
3. **Database Layer**: CRUD actions are executed via SQLModel engine ([database.py](file:///home/njaal/git/tascam/tascam_app/database.py)) -> SQLite/Postgres DB
4. **Ingestion Pipeline**: Command Line interface ([process.py](file:///home/njaal/git/tascam/process.py)) -> Audio processor ([audio_processor.py](file:///home/njaal/git/tascam/tascam_app/audio_processor.py)) -> database updates and MP3 generation ([data/clips](file:///home/njaal/git/tascam/data/clips))

## E. Key Commands
* Test: `uv run pytest`
* Dev Server: `uv run uvicorn tascam_app.web:app --host 0.0.0.0 --reload`
* Ingestion: `uv run python process.py import-dir /path/to/wav/files`

