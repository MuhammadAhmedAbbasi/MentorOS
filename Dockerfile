FROM python:3.12-slim

WORKDIR /app

# Install system build deps required by asyncpg
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files pip needs to resolve and install the package.
# This layer is cached as long as pyproject.toml and README.md are unchanged.
COPY pyproject.toml README.md ./

# Copy source so the editable install resolves the mentoros package.
COPY src/ src/

# Install runtime dependencies only (no dev extras in the image).
RUN pip install --no-cache-dir -e .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "mentoros.main:app", "--host", "0.0.0.0", "--port", "8000"]
