import os

bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:8000')
workers = int(os.environ.get('GUNICORN_WORKERS', '3'))
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
