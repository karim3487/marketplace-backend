# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

# Install dependencies
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app

# Install dependencies first for better caching
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Then copy the rest of the application
ADD . /app

# Final stage
FROM python:3.12-alpine
WORKDIR /app

# Copy the environment from the builder
COPY --from=builder /app /app

# Set up environment variables
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
