# AI Development Workflow - Marketplace Backend

## Infrastructure Phase (Stage 1)

### Phase 1.1: Docker Compose & Environment

**Decision**: Configure a production-ready local stack with Postgres 16 and MinIO.

- **Postgres**: Used `postgres:16-alpine` for minimal footprint. Persistence via `./volumes/pg_data`.
- **MinIO**: S3-compatible storage for product images. Persistence via `./volumes/minio_data`.
- **Backend Service**: Configured to build from `./marketplace-backend`, using `.env` for secrets.
- **Frontend Service**: Configured to build from `./marketplace-frontend`, using `.env` for secrets.

**Iteration**:

1. Defined `docker-compose.yaml` with 4 services (`postgres`, `minio`, `backend`, `frontend`).
2. Created `.env.example` with standard defaults (`admin`/`changeme`) and asyncpg connection strings.

## Phase 2: Backend Structure Setup

### Phase 2.1: FastAPI Boilerplate

**Decision**: Adopt the `fastapi-templates` structure focusing on pure async operations and strict typings with SQLAlchemy 2.0.

- **Core**: Added `api_v1_prefix`, `project_name`, and MinIO properties to `core/config.py`.
- **Models**: Initialized `models/base.py` with SQLAlchemy 2.0 `DeclarativeBase`.
- **Repositories**: Created a generic asynchronous `BaseRepository` in `repositories/base.py` emphasizing `session.execute` and Pydantic v2 `model_dump()`.
- **API**: Established the initial `api/v1/router.py` holding `api_router`, along with `api/dependencies.py` defining an async session dependency.
- **Main**: Bootstrapped FastAPI in `main.py` utilizing `asynccontextmanager` for database teardown setup, added CORS, and mounted the API router.

### Phase 2.2: Directory Restructuring

**Decision**: Wrap all core logic within an `app/` envelope to fully align with the `fastapi-templates` structure (and the user's specific request).

- Mapped all directories (`api`, `core`, `models`, `repositories`, `schemas`, `services`) and `main.py` into the `app/` folder.
- Updated all absolute internal imports from `module.foo` to `app.module.foo` to guarantee correct resolution when running via `uv run fastapi dev app/main.py`.

**Iteration**:
Scaffolded empty layers for `services`, `schemas`, and `endpoints`. Cleaned files using `ruff` with strict Python 3.12 targets and type hint requirements enforced.

## Phase 3: Database Models and Seeding

**Decision**: Implement strict SQLAlchemy 2.0 models and configure an automated seeding pipeline.

- **Models**: Created `Product`, `ProductAttribute`, `Seller`, `Offer` mapped to UUID primary keys and defined tight database cascades (`delete-orphan`, `CASCADE`).
- **Alembic**: Updated `alembic/env.py` pointing it to `app.models.base`. Used `sys.path` injection and `# noqa: E402` to manage import resolution seamlessly.
- **Data Seeding**: Built `scripts/seed.py` wrapping standard CRUD operations natively. Implemented specific logic to spawn 100 base items and map their `delivery_date` exactly bounded between March 2 and 8, 2026.

**Iteration Process**:
Created models -> Patched Alembic -> Wrote Seed script -> Formatted code with `uvx ruff format` -> Iteratively fixed `datetime.UTC` typing errors and Alembic's top-level import warnings.

## Phase 4: Business Logic and API Router Implementation

**Decision**: Configure explicit HTTP routes utilizing custom BaseRepository and async-native implementations conforming to the OpenAPI specification logic.

- **AI Tools Used**: Base logic relied firmly on `@fastapi-templates` recommendations.
- **Storage Service (`aiobotocore`)**: Created `app/services/storage.py` avoiding sync bounds by integrating `aiobotocore` asynchronously to communicate with `MinIO`. Yields publicly reachable URLs constructed from container bindings.
- **Security Dependency**: `app/core/security.py` abstracts JWT signing and extraction using basic symmetric HS256 algorithms and standard HTTPBearer dependency mappings.
- **Pydantic Validation**: Assembled strict Data Transfer Objects inside `app/schemas/models.py`. Implemented ConfigDict for arbitrary objects avoiding Optionals and relying exclusively on robust runtime mapping.
- **Infinite Scrolling API**: Formulated dynamic relations traversal in `GET /v1/public/products` fetching relations pre-calculated to emit correctly localized explicit fields (`nearest_delivery_date`) outside of raw DB execution, keeping responses completely atomic.
- **Sorting Mechanisms**: The product detail endpoint implicitly filters out `Offer` sub-nodes leveraging `order_by` chains matching `price` and `delivery_date` inputs seamlessly avoiding nested Python manipulation.
- **Routing Configuration**: Nested routers linked logically into `app/api/v1/router.py` bypassing circular resolution and correctly tagging OpenAPI schemas. `pyproject.toml` modified to bypass B008 lints traditionally caused by `Depends()` injection structures.

**Iteration Process**:
Draft properties -> Generated Pydantic Schemas -> Connected logic into Custom Repositories (`product`, `offer`) -> Designed abstract `public`/`admin` routers implementing logic bounds constraints correctly -> Validated configurations and fixed residual `B904` and `E501` exception handling format lints via `uvx ruff` -> Restored several zero-byte repository and endpoint files detected during local verification -> Fixed `MissingGreenlet` and `AttributeError` in detailed view by using a separate sorted query and `set_committed_value` to safely attach offers -> Moved MinIO bucket initialization to infrastructure-level `minio-setup` service using `mc` client for production alignment -> Refactored all Schemas, Repositories, and Endpoints for full OpenAPI parity (Nested Money objects, PaginatedResponse wrappers, and custom ErrorResponse handlers).

## Phase 5: Quality Assurance & Global Exceptions

**Decision**: Enforce OpenAPI `ErrorResponse` schema completely across the application by centralizing error catching and logging.

- **AI Tools Used**: Base AI Models using `fastapi-pro` patterns.
- **Iteration Process**: Plan -> Generation -> Verification -> Ruff Check -> Smoke Testing
- **Checks Performed**:
  - `uvx ruff check --fix .` and `uvx ruff format .` guarantees formatting
  - Run asynchronous isolated smoke tests using `pytest` mapped locally.
- **Engineering Decisions & Reasoning**: Built global catchalls `marketplace_exception_handler` and a custom Pydantic `RequestValidationError` handler inside `app.main.py`. This isolates HTTP bounds checks entirely out of explicit route functions into clean, dedicated custom exception raisings mapped from `app/core/exceptions.py`. Ensures strict adherence to custom `ErrorResponse` structures without polluting endpoints.

## Phase 6: Business Logic Layer (Service Pattern)

**Decision**: Introduced a dedicated `services/` layer to decouple complex orchestration and business rules from the HTTP handlers, ensuring "thin" controllers as per `fastapi-templates` best practices.

- **AI Tools Used**: Base AI Models using `fastapi-templates` patterns.
- **Iteration Process**: Plan -> Generation -> Verification -> Fixed zero-byte files -> Verified via smoke tests.
- **Checks Performed**:
  - Validated that `ProductService` correctly orchestrates dual S3 uploads and DB updates.
  - Verified `AuthService` handles JWT and password hashing consistently.
  - Smoke tests (`make test`) pass 100%.
- **Engineering Decisions & Reasoning**: Handlers now only manage API-specific logic (receiving requests, calling services, formatting responses). This improves testability (services can be unit tested in isolation) and allows for reuse of logic across different entry points (e.g., CLI tools or background workers) without duplicating HTTP-specific code.

## Phase 7: Repository Fixes and Eager Loading

**Decision**: Resolved `MissingGreenlet` errors specifically in the Product CRUD operations by implementing specialized eager loading in the repository layer.

- **AI Tools Used**: Base AI models for root cause analysis.
- **Iteration Process**: Diagnosis -> Plan -> Implementation -> Verification.
- **Checks Performed**:
  - Manual creation and update of products verified via OpenAPI docs (Swagger).
  - Verified no regressions in Listing/Public API.
- **Engineering Decisions & Reasoning**: Switched from generic `db.refresh()` to a specialized `self.get()` call utilizing `selectinload` for `Product.attributes`. This ensures that Pydantic serialization doesn't trigger lazy-loading calls outside the established async session, maintaining strict async compliance.

## Phase 8: Sellers Administration & Expanded Product Schema

**Decision**: Implement full CRUD for Sellers and enhance Product Detail API to support offers management in the admin dashboard.

- **AI Tools Used**: Base AI models for route/schema generation.
- **Iteration Process**: Schema Update -> Router Expansion -> OpenAPI Regeneration -> Verification.
- **Checks Performed**:
  - `uvx ruff check --fix .` ensures strict async and PEP8 compliance.
  - Manual PUT/DELETE verification via Swagger.
- **Engineering Decisions & Reasoning**: Expanded `SellerUpdate` and added `PUT`/`DELETE` endpoints to `admin_sellers.py` to allow vendor lifecycle management. Upgraded `read_product` in `admin_products.py` to use `ProductDetailResponse`, enabling the frontend to manage a product's list of offers and their respective vendors from a single view.
