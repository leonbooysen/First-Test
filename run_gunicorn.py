"""Production entrypoint for Gunicorn (AWS Fargate, etc.)."""
import os

# Fargate / ALB set PORT (default 8080 for Fargate)
port = int(os.environ.get("PORT", "8080"))
bind = f"0.0.0.0:{port}"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info").lower()

# Writable dirs for non-root container (avoids [Errno 13] Permission denied on control server / worker tmp)
worker_tmp_dir = "/tmp"
# Disable control socket in container (no gunicornc needed; avoids Permission denied on socket creation)
no_control_socket = True
pidfile = None  # don't write pid file by default in container
