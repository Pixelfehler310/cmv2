FROM python:3.11-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# Path is relative to the context (root)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Expose port
EXPOSE 8000


FROM base AS runtime

# Start with reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


FROM base AS test

RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && npm install --global json-schema-to-typescript@13.1.1 \
    && rm -rf /var/lib/apt/lists/*

# Default test command for one-shot runs (overridable in compose).
CMD ["python", "-m", "pytest", "tests", "-q"]
