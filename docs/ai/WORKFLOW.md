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

## Phase 9: Dockerization & Orchestration

**Decision**: Containerize both services to allow unified execution via `docker compose`.

- **Backend Dockerfile**: Used `ghcr.io/astral-sh/uv:python3.12-alpine` for ultra-fast, multi-stage builds. Leveraged `uv sync` for dependency isolation and byte-code compilation.
- **Frontend Dockerfile**: Implemented a multi-stage build using `node:20-alpine` for compilation and `nginx:stable-alpine` for serving the static production assets.
- **Docker Compose**: Updated root `docker-compose.yaml` with correct build contexts (`../marketplace-backend`, `../marketplace-frontend`) and mapped frontend internal port 80 to host 5173 for parity with dev environment.

**Iteration Process**:
Created Dockerfiles -> Updated Compose contexts -> Aligned Port Mappings -> Logged Engineering Decisions.

**Checks Performed**:
- Verified `uvicorn` and `nginx` CMD syntax.
- Confirmed `depends_on` health-check chains in `docker-compose.yaml`.
- Validated build context paths relative to the `marketplace-stack` folder.

**Engineering Decisions & Reasoning**: 
Chose `uv-alpine` for the backend to maintain the "strictly uv" requirement while minimizing image size. Used Nginx for the frontend to mirror a production-ready static hosting environment, moving away from Vite's dev server for the containerized stack.

**Bugfix (Docker Build)**:
Identified a `uv sync --frozen` failure during Docker build caused by a mismatch between `pyproject.toml` and `uv.lock` after moving `pyrefly` to `dev-dependencies`. 
- **Action**: Ran `uv lock` to update the lockfile, ensuring production builds skip `pyrefly` as expected when using the `--no-dev` flag.

**Bugfix (Docker Runtime)**:
Encountered `no such file or directory` when executing `uvicorn` in the container. 
- **Cause**: The local macOS `.venv` was being copied into the container, overwriting the Linux-compatible one created during the build.
- **Action**: Created `.dockerignore` for both backend and frontend to exclude `.venv`, `node_modules`, and other local artifacts.

**Bugfix (Frontend API URL)**:
Frontend was making relative requests to its own port (5173).
- **Cause**: Lack of Nginx reverse proxy in the production container (unlike the Vite dev server proxy).
- **Action**: Created a custom `nginx.conf` in the frontend that proxies `/api` to the `backend` Docker service and updated the frontend `Dockerfile`.

## Phase 10: MinIO Browser Accessibility Fix

**Decision**: Resolve the issue where images uploaded to MinIO were inaccessible to the browser due to the backend using an internal Docker network endpoint.

- **New Environment Variable**: Introduced `MINIO_BROWSER_ENDPOINT`, allowing the backend to separate its internal communication with MinIO from the URLs provided to the browser.
- **Storage Service Refactor**: Modified `app/services/storage.py` to use `MINIO_ENDPOINT` for internal S3 operations while generating public URLs using `MINIO_BROWSER_ENDPOINT`.
- **Configuration Update**: Added `minio_browser_endpoint` to `app/core/config.py` with proper Pydantic validation.
- **Environment Alignment**: Updated `.env` and `.env.example` in both `marketplace-backend` and `marketplace-stack` repositories.

**Iteration Process**:
Diagnosis -> Plan -> Code Implementation -> Env Updates -> Ruff Verification -> Documentation.

**Checks Performed**:
- `uv run ruff check` and `uv run ruff format` on modified files.
- Verified that `MINIO_BROWSER_ENDPOINT` defaults to `MINIO_ENDPOINT` if not provided, ensuring backward compatibility.

**Engineering Decisions & Reasoning**: 
By decoupling the internal and external endpoints, we ensure that the backend can reliably communicate with MinIO within the Docker network (`http://minio:9000`) while giving the frontend valid URLs that work in a standard browser environment (`http://localhost:9000`).

## Phase 11: HEIC Image Support

**Decision**: Enable support for HEIC (High Efficiency Image Container) files to ensure compatibility with modern mobile uploads.

- **New Dependency**: Added `pillow-heif` to handle decoding of HEIF/HEIC images.
- **Image Utility Update**: Modified `app/utils/image.py` to register the HEIF opener, allowing `PIL.Image.open()` to natively process `.heic` files.

**Iteration Process**:
Plan -> Add Dependency (`uv add`) -> Register Opener -> Ruff Lint/Format -> Documentation.

**Checks Performed**:
- `uv tool run ruff` verified import sorting and formatting.
- Dependency verified in `pyproject.toml`.

**Engineering Decisions & Reasoning**: 
HEIC is the default format for many modern smartphones. By integrating `pillow-heif` and registering it globally via `register_heif_opener()`, we transparently extend our existing thumbnail generation logic to support these files without changing the core processing pipeline.

## Phase 12: Nginx Request Body Size Limit

**Decision**: Increase Nginx `client_max_body_size` to `20M` to allow high-resolution image and HEIC uploads.

- **Configuration Update**: Modified `marketplace-frontend/nginx.conf` to add `client_max_body_size 20M;`.

**Iteration Process**:
Plan -> Modify `nginx.conf` -> Documentation.

**Checks Performed**:
Corrected the `server` block configuration.

**Engineering Decisions & Reasoning**: 
The default Nginx limit is 1MB, which is insufficient for modern high-resolution photos and compressed HEIC files (often 2-5MB). Setting the limit to 20MB provides ample headroom for typical marketplace image uploads while still protecting the server from excessively large requests.

## Phase 13: HEIC Original Image Browser Compatibility

**AI Tools Used**: Antigravity (Gemini)

**Problem**: Thumbnails (generated via `create_thumbnail`) displayed correctly because they are converted to JPEG. However, the original full-size HEIC files were uploaded as-is, and browsers cannot render HEIC natively.

**Solution**:
- Added `convert_to_web_format()` in `app/utils/image.py` — converts non-web-safe images (HEIC, TIFF, etc.) to JPEG before upload, while passing through web-safe formats (JPEG, PNG, GIF, WebP, SVG) unchanged.
- Updated `product_service.py` `upload_image()` to call `convert_to_web_format()` on the original file before uploading to MinIO.

**Iteration Process**: Investigate → Implement conversion utility → Integrate into upload pipeline → Ruff check → Documentation.

**Checks Performed**: `uvx ruff check` and `uvx ruff format` — all checks passed.

**Engineering Decisions & Reasoning**: 
Converting at upload time means every stored original is browser-renderable. The raw HEIC bytes are still passed to `create_thumbnail()` since `pillow-heif` handles them. Quality is set to 90 for originals (vs 85 for thumbnails) to preserve detail.

## Phase 14: Universal AVIF Conversion

**AI Tools Used**: Antigravity (Gemini)

**Decision**: Convert ALL uploaded images (originals and thumbnails) to AVIF format.

**Changes**:
- Replaced `convert_to_web_format()` with `convert_to_avif()` in `app/utils/image.py` — converts **every** image to AVIF regardless of input format.
- Updated `create_thumbnail()` to output AVIF (quality 60) instead of JPEG.
- Updated `product_service.py` to use `convert_to_avif()` and set `image/avif` content type.

**Iteration Process**: Verify Pillow AVIF support → Rewrite utils → Update service → Ruff check → Documentation.

**Checks Performed**: `uvx ruff check` and `uvx ruff format` — all checks passed. Verified `AVIF` in Pillow's registered extensions.

**Engineering Decisions & Reasoning**: 
AVIF provides superior compression (up to 50% better than WebP or JPEG) while maintaining high visual quality. By standardizing on AVIF for both originals and thumbnails, we significantly reduce storage requirements and improve page load times for end-users.

## Phase 15: Offer Audit Logs (Fix)

**AI Tools Used**: Antigravity (Gemini)

**Problem**: Audit logs for `OFFER_ADD` and `OFFER_REMOVE` actions were missing in `admin_offers.py`, leading to incomplete product history.

**Solution**:
- Implemented `OFFER_ADD` audit logging in `create_offer` endpoint.
- Implemented `OFFER_REMOVE` audit logging in `delete_offer` endpoint.
- Logs include `product_id`, `admin_username`, and detailed `changes` (serialized offer data or IDs).

**Iteration Process**: Investigation -> Identification of missing logic -> Code implementation -> Verification of file persistence -> Documentation.

**Checks Performed**:
- Verified `admin_offers.py` content to ensure logic is correctly applied.
- Ran `ruff` (manually verified code style since `uv run ruff` had environment issues).

**Engineering Decisions & Reasoning**: 
Audit logging is critical for marketplace integrity. By capturing offer changes in the `ProductAuditLog` table, admins can track which offers were added or removed and by whom, maintaining a full audit trail for every product.

## Phase 16: Async Image Processing Optimization

**AI Tools Used**: Antigravity (Gemini)

**Decision**: Offload CPU-bound image encoding tasks (AVIF conversion and thumbnail generation) to a `ProcessPoolExecutor` to prevent event loop blocking.

**Changes**:
- **Executor Integration**: Added a global `ProcessPoolExecutor` in `app/utils/image.py`.
- **Async Offloading**: Wrapped synchronous Pillow operations (`convert_to_avif`, `create_thumbnail`) in `loop.run_in_executor()`.
- **Strictly Async Compliance**: Ensured all image processing functions are now `async def` and correctly called within the `ProductService`.
- **Import Standardization**: Switched to `import asyncio` (built-in) instead of `from app.core.utils import asyncio`.

**Iteration Process**: Performance Audit -> Execution Strategy Plan -> Implementation -> Ruff Validation -> Documentation.

**Checks Performed**:
- Verified `ruff check` and `ruff format` passed without issues.
- Confirmed use of `asyncio.get_running_loop()` for modern runtime compatibility.

**Engineering Decisions & Reasoning**: 
Image processing is a CPU-intensive task that blocks the Python event loop, significantly reducing the throughput of an asynchronous FastAPI application. By utilizing a `ProcessPoolExecutor`, we move these operations to separate worker 

---

### Audit Logging for Image Uploads

**AI Tools Used**: `@fastapi-pro`, `@python-pro`

**Iteration Process**: Plan -> Implementation -> Ruff Validation -> Smoke Testing -> Documentation.

**Checks Performed**:
- `ruff check --fix` and `ruff format` passed.
- Smoke tests passed via `pytest tests/test_smoke.py`.
- Manual inspection of `ProductService._create_audit_log` integration.

**Engineering Decisions & Reasoning**: 
Implemented audit logging for the `IMAGE_UPLOAD` action to maintain a traceable history of product assets. Additionally, updated the administrative endpoints (`create`, `update`, `delete`, `upload_image`) to correctly capture the `admin_username` from the authentication context, ensuring that audit logs are attributed to the correct performing user.

## [2026-03-11] - Audit Logging for Image Uploads
- **AI Tools Used**: `fastapi-pro`, `vue-tsc`, `ruff`.
- **Iteration Process**: Plan -> Backend Implementation (ProductService & Repository) -> Frontend Implementation (ProductEditPage refresh) -> Verification (ruff).
- **Checks Performed**: `ruff check --fix`, `ruff format`.
- **Engineering Decisions & Reasoning**: Chose to log image uploads as "UPDATE" actions in the existing audit log system. Fetched the performing user's name from the database to provide clear attribution in the log message. Implemented a centralized `refreshData` helper in the frontend to ensure UI consistency.
