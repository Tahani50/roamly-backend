# Roamly Backend Architecture

Roamly Backend follows a layered architecture designed to keep HTTP handling, business logic, database access, persistence models, API contracts, and external services separate. Each layer has a clear responsibility and may depend only on the layers below it. The goal is to make the codebase easier to test, maintain, and extend as new features are added.

## Application Entry Point — `app/main.py`

`app/main.py` is the application entry point. It creates the FastAPI application, registers routers, attaches global middleware, and configures application-level startup or shutdown behavior when needed. It may import the main API router and application-wide configuration. Business rules, database queries, feature-specific logic, SQLAlchemy models, and third-party API implementation must never be placed here.

## API Layer — `app/api/`

The API layer is responsible for HTTP concerns. It defines endpoints, reads path/query/body parameters, applies authentication or reusable FastAPI dependencies, calls the appropriate service, converts results into response schemas, and maps known application errors to HTTP responses. `app/api/deps.py` contains reusable request dependencies, while `app/api/v1/router.py` combines the versioned endpoint routers and `app/api/v1/endpoints/` contains feature-specific route handlers. Database queries, SQLAlchemy session logic, business rules, and direct communication with external APIs must never be implemented inside endpoint files.

## Service Layer — `app/services/`

The service layer contains the application's business logic and use-case orchestration. A service decides what should happen when the user performs an action, validates rules that belong to the business domain, coordinates one or more repositories, and may coordinate external integrations. For example, a trip service may load a trip, verify that the requesting user owns it, retrieve related activities, and request place information from an integration. Services must never contain HTTP-specific code such as FastAPI `Request`, `Response`, route decorators, or HTTP status codes. They must also never contain raw SQL or direct database queries that belong in repositories.

## Repository Layer — `app/repositories/`

The repository layer is responsible for database access. Repositories contain queries and persistence operations such as finding a trip by ID, listing a user's trips, creating a record, updating a record, or deleting a record. Repositories work with SQLAlchemy sessions and SQLAlchemy models and return database entities or well-defined persistence results to the service layer. Business rules, HTTP behavior, Pydantic response formatting, and calls to external services must never be placed in repositories.

## Model Layer — `app/models/`

The model layer contains SQLAlchemy ORM models representing persisted database entities and their relationships. Examples include `User`, `Trip`, `Activity`, and `Expense`. Models define database columns, foreign keys, constraints, and ORM relationships. Models must never handle HTTP requests, perform database queries, call repositories or services, communicate with external APIs, or contain API response formatting. A model describes how data is stored; it does not decide how a feature behaves.

## Schema Layer — `app/schemas/`

The schema layer contains Pydantic models that define the application's external and internal data contracts. Schemas validate incoming request data and control the structure of outgoing API responses. Request and response schemas should be separate when their requirements differ; for example, a `TripCreate` schema may accept a destination and dates, while a `TripResponse` schema may also expose an ID and creation timestamp. Schemas must never perform database queries, contain SQLAlchemy persistence logic, call services or repositories, or contain business workflows.

## Database Infrastructure — `app/db/`

The database layer contains infrastructure required to connect SQLAlchemy to the database. `session.py` is responsible for engine and session configuration, while `base.py` provides the declarative base and related shared ORM setup. This layer may configure the database connection and expose session-building utilities to the repository or dependency layer. Feature-specific queries, business rules, endpoint code, and API schemas must never be placed here.

## Core Layer — `app/core/`

The core layer contains application-wide infrastructure and configuration that does not belong to a specific feature. `config.py` handles environment-based settings, `security.py` contains shared authentication and security utilities, `exceptions.py` defines application-level exceptions, and `responses.py` may define reusable response helpers or common response structures. Core code should be reusable across the application and must never contain feature-specific workflows such as creating a trip, calculating expenses, or building an itinerary. It must also avoid depending on API endpoint modules.

## Integration Layer — `app/integrations/`

The integration layer contains adapters for external systems such as Google Places, weather providers, Firebase, email services, or other third-party APIs. Each integration is responsible for translating the external provider's API into a clean interface that the service layer can use. Provider-specific URLs, authentication headers, SDK calls, request payloads, and response parsing belong here. Endpoint handling, application business rules, direct database persistence, and SQLAlchemy queries must never be placed in this layer.

## Tests — `tests/`

The test layer verifies application behavior without becoming part of production code. `tests/unit/` contains focused tests for individual services, repositories, utilities, or other isolated components, while `tests/integration/` verifies interactions between multiple parts of the system such as the API, database, and repository layers. `conftest.py` contains shared pytest fixtures and test configuration. Production behavior, shared application utilities, and code required by the running application must never be implemented only inside the tests directory.

## Database Migrations — `alembic/`

The `alembic/` directory contains database migration scripts and Alembic configuration generated as the database schema evolves. Migrations describe structural changes such as adding tables, columns, indexes, or constraints and allow environments to move between known database versions. Application queries, business logic, request validation, API endpoints, and runtime database operations must never be implemented as migrations.

## Project Configuration Files

`.env.example` documents the environment variables required to run the application without containing real secrets. `requirements.txt` records Python package dependencies. `ARCHITECTURE.md` documents the architectural rules described here. Real passwords, API keys, access tokens, private credentials, and machine-specific secrets must never be committed to these files or to the repository.

# Dependency Rule

Dependencies must flow inward from delivery and orchestration code toward persistence and infrastructure, never in the opposite direction.

```text
API Endpoint
     │
     ▼
   Service
     │
     ▼
 Repository
     │
     ▼
   Model
     │
     ▼
 Database
```

Schemas are used at the API boundary to validate input and serialize output:

```text
Request
   │
   ▼
Request Schema
   │
   ▼
Endpoint
   │
   ▼
Service
   │
   ▼
Repository
   │
   ▼
Model / Database
   │
   ▼
Service
   │
   ▼
Response Schema
   │
   ▼
HTTP Response
```

External integrations are called by services when a use case requires information or behavior outside Roamly:

```text
Endpoint
   │
   ▼
Service ─────────► Integration
   │
   ▼
Repository
```

The direction matters. An endpoint may depend on a service, but a service must not depend on an endpoint. A service may depend on a repository, but a repository must not depend on a service. A repository may depend on SQLAlchemy models and database infrastructure, but models must not depend on repositories. Integrations may be used by services, but integrations must not call API endpoints.

# Worked Request Trace

Consider the request:

```http
GET /api/v1/trips/42
```

Assume the user is requesting the trip whose ID is `42`.

## 1. Request reaches the endpoint

The request is handled by the route defined in:

```text
app/api/v1/endpoints/trips.py
```

Conceptually, the endpoint is responsible for HTTP concerns:

```python
@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int,
    trip_service: TripService = Depends(get_trip_service),
):
    trip = await trip_service.get_trip(trip_id)
    return TripResponse.model_validate(trip)
```

The endpoint reads `trip_id` from the URL and delegates the actual operation to the service. It does not query the database itself.

The flow is now:

```text
GET /trips/42
      │
      ▼
trips.py endpoint
```

## 2. Endpoint calls the service

The endpoint calls something such as:

```text
app/services/trip_service.py
```

Conceptually:

```python
class TripService:
    def __init__(self, trip_repository):
        self.trip_repository = trip_repository

    async def get_trip(self, trip_id: int):
        trip = await self.trip_repository.get_by_id(trip_id)

        if trip is None:
            raise TripNotFoundError(trip_id)

        return trip
```

The service owns the use-case behavior. It asks the repository for the trip and applies application rules, such as deciding what should happen when the trip does not exist.

The flow becomes:

```text
GET /trips/42
      │
      ▼
Endpoint
      │
      ▼
TripService.get_trip(42)
```

## 3. Service calls the repository

The service delegates persistence to:

```text
app/repositories/trip_repository.py
```

Conceptually:

```python
class TripRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_id(self, trip_id: int):
        return await self.session.get(Trip, trip_id)
```

The repository knows how to retrieve the entity from the database. It does not decide whether a missing trip should become a `404` response; that decision belongs above the persistence layer.

The flow is now:

```text
GET /trips/42
      │
      ▼
Endpoint
      │
      ▼
TripService
      │
      ▼
TripRepository.get_by_id(42)
```

## 4. Repository works with the SQLAlchemy model

The repository queries the SQLAlchemy model defined in:

```text
app/models/trip.py
```

Conceptually:

```python
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    destination = Column(String, nullable=False)
```

The model describes how the trip exists in the database. SQLAlchemy loads the row where `id = 42` and returns a `Trip` ORM object to the repository.

The flow is now:

```text
GET /trips/42
      │
      ▼
Endpoint
      │
      ▼
TripService
      │
      ▼
TripRepository
      │
      ▼
Trip SQLAlchemy model
      │
      ▼
Database
```

The result then travels back upward:

```text
Database
    │
    ▼
Trip model instance
    │
    ▼
Repository
    │
    ▼
Service
```

## 5. The result is converted to a response schema

After the service returns the trip, the endpoint serializes it using a schema defined in:

```text
app/schemas/trip.py
```

For example:

```python
class TripResponse(BaseModel):
    id: int
    title: str
    destination: str

    model_config = ConfigDict(from_attributes=True)
```

The response schema controls what the API exposes. The SQLAlchemy model might contain fields that must not be returned publicly, but `TripResponse` exposes only the fields that belong in the API contract.

The complete request path is therefore:

```text
GET /api/v1/trips/42
          │
          ▼
app/api/v1/endpoints/trips.py
          │
          ▼
app/services/trip_service.py
          │
          ▼
app/repositories/trip_repository.py
          │
          ▼
app/models/trip.py
          │
          ▼
Database
          │
          ▼
Trip ORM instance
          │
          ▼
Repository
          │
          ▼
Service
          │
          ▼
app/schemas/trip.py
          │
          ▼
TripResponse
          │
          ▼
HTTP 200 JSON response
```

The client ultimately receives something like:

```json
{
  "id": 42,
  "title": "Riyadh Weekend",
  "destination": "Riyadh"
}
```

This trace demonstrates the dependency rule rather than only stating it: the endpoint handles HTTP, the service owns the use case, the repository owns the database operation, the model represents persisted data, and the schema controls the public response. No layer performs the responsibility of another layer.
