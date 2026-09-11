# Roamly — Backend

Shared API for the Roamly travel planner, supporting the iOS, Flutter and Android applications.

Roamly helps users organize trips, daily itineraries, activities, expenses, packing lists, saved places and travel companions.

## Status

🚧 In development — started September 2026

## Tech stack

Python · FastAPI · PostgreSQL · SQLAlchemy · Alembic · Firebase Admin · Pytest · Docker

## Architecture

Roamly Backend follows a layered architecture that separates API handling, business logic, database access, persistence models, schemas, and external integrations.

The main dependency flow is:

`Endpoint → Service → Repository → Model / Database`

For full details, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Getting started

Clone the repository:

```bash
git clone https://github.com/Tahani50/roamly-backend.git
cd roamly-backend
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

Create your local environment file:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder values with your real local configuration and API credentials.

Run the FastAPI development server:

```bash
fastapi dev app/main.py
```

Once the server is running, open:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "roamly-api",
  "environment":"development"
}
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```


## API documentation

TODO — endpoints, authentication and request examples

## Testing

TODO — unit and integration test instructions

## Related repositories

* [roamly-ios](https://github.com/Tahani50/roamly-ios) — Native iOS app built with Swift / SwiftUI
* [roamly-flutter](https://github.com/Tahani50/roamly-flutter) — Cross-platform app built with Flutter
* [roamly-android](https://github.com/Tahani50/roamly-android) — Native Android app built with Kotlin / Jetpack Compose

