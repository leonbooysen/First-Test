# MFA Reset Portal - production image for AWS Fargate
# Python 3.12 + Microsoft ODBC Driver 18 for SQL Server

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Runtime stage ---
FROM python:3.12-slim-bookworm

# Install Microsoft ODBC Driver 18 for SQL Server (Debian 12) via repo .deb
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -sSL -o /tmp/packages-microsoft-prod.deb https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for Fargate
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

# Copy installed packages from builder (chown for app user)
COPY --from=builder --chown=app:app /root/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Copy application
COPY --chown=app:app . .

USER app

# Fargate / ALB use PORT (default 8080); health check at /health
ENV PORT=8080 \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1

EXPOSE 8080

# Gunicorn reads PORT from env via run_gunicorn.py
CMD ["gunicorn", "-c", "run_gunicorn.py", "app:app"]
