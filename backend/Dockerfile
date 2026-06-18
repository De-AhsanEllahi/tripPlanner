FROM python:3.12-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies (minimal but safe for Django + psycopg)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (better caching)
COPY pyproject.toml uv.lock /app/

RUN pip install --upgrade pip && \
    pip install uv && \
    uv pip install --system -r pyproject.toml

# Copy backend code
COPY . /app/

EXPOSE 8000

# Default dev command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]