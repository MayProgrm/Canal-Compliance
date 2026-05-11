# Guía de Despliegue - Canal de Denuncias

Saludos a Tecnologias de la informacion y Seguridad informatica.

Esta guía proporciona instrucciones detalladas para desplegar el sistema Canal de Denuncias en diferentes entornos de producción.

##  Opciones de Despliegue

### 1. Servidor VPS/Dedicado (Ubuntu/CentOS)
### 2. Heroku (PaaS)
### 3. Docker (Containerización)
### 4. AWS/Azure/GCP (Cloud)

---

##  Despliegue en Servidor VPS (Ubuntu 20.04+)

### Paso 1: Preparación del Servidor

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib supervisor git

sudo adduser canal_denuncias
sudo usermod -aG sudo canal_denuncias
```

### Paso 2: Configurar PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE canal_denuncias;
CREATE USER canal_user WITH PASSWORD 'password_seguro';
ALTER ROLE canal_user SET client_encoding TO 'utf8';
ALTER ROLE canal_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE canal_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE canal_denuncias TO canal_user;
\q
```

### Paso 3: Configurar la Aplicación

```bash
sudo su - canal_denuncias

git clone <repository-url> /home/canal_denuncias/canal_denuncias
cd /home/canal_denuncias/canal_denuncias

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install psycopg2-binary gunicorn

cp .env.example .env
nano .env
```

### Paso 4: Configuración de Producción (.env)

```bash
SECRET_KEY=clave-super-secreta-de-50-caracteres-minimo
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,IP-del-servidor

DATABASE_URL=postgresql://canal_user:password_seguro@localhost:5432/canal_denuncias

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password

MAX_UPLOAD_SIZE=10485760
ALLOWED_UPLOAD_EXTENSIONS=pdf,doc,docx,txt,jpg,jpeg,png,gif,mp4,avi,mp3,wav,zip,rar

SECURE_SSL_REDIRECT=True
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Paso 5: Preparar Django

```bash
python manage.py makemigrations
python manage.py migrate

python manage.py createsuperuser

python manage.py collectstatic --noinput

mkdir -p /home/canal_denuncias/canal_denuncias/media/complaints
chmod 755 /home/canal_denuncias/canal_denuncias/media
```

### Paso 6: Configurar Gunicorn

```bash
nano /home/canal_denuncias/canal_denuncias/gunicorn.conf.py
```

```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
user = "canal_denuncias"
group = "canal_denuncias"
tmp_upload_dir = None
errorlog = "/home/canal_denuncias/canal_denuncias/logs/gunicorn_error.log"
accesslog = "/home/canal_denuncias/canal_denuncias/logs/gunicorn_access.log"
loglevel = "info"
```

### Paso 7: Configurar Supervisor

```bash
sudo nano /etc/supervisor/conf.d/canal_denuncias.conf
```

```ini
[program:canal_denuncias]
command=/home/canal_denuncias/canal_denuncias/venv/bin/gunicorn canal_denuncias.wsgi:application -c /home/canal_denuncias/canal_denuncias/gunicorn.conf.py
directory=/home/canal_denuncias/canal_denuncias
user=canal_denuncias
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/canal_denuncias/canal_denuncias/logs/supervisor.log
environment=PATH="/home/canal_denuncias/canal_denuncias/venv/bin"
```

```bash
mkdir -p /home/canal_denuncias/canal_denuncias/logs

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start canal_denuncias
```

### Paso 8: Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/canal_denuncias
```

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Redirigir HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com www.tu-dominio.com;
    
    # Certificados SSL (configurar con Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Configuración SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Configuración de archivos estáticos
    location /static/ {
        alias /home/canal_denuncias/canal_denuncias/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /home/canal_denuncias/canal_denuncias/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Proxy a Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Límites de tamaño de archivo
    client_max_body_size 10M;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/canal_denuncias /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Paso 9: Configurar SSL con Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx

sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

sudo crontab -e
0 12 * * * /usr/bin/certbot renew --quiet
```

---

##  Despliegue con Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "canal_denuncias.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: canal_denuncias
      POSTGRES_USER: canal_user
      POSTGRES_PASSWORD: password_seguro
    ports:
      - "5432:5432"

  web:
    build: .
    command: gunicorn canal_denuncias.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://canal_user:password_seguro@db:5432/canal_denuncias

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Comandos Docker

```bash
# Construir y ejecutar
docker-compose up --build -d

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Recopilar archivos estáticos
docker-compose exec web python manage.py collectstatic --noinput

# Ver logs
docker-compose logs -f web
```

---

##  Despliegue en Heroku

### Preparación

```bash
# Instalar Heroku CLI
# Crear Procfile
echo "web: gunicorn canal_denuncias.wsgi:application" > Procfile

# Crear runtime.txt
echo "python-3.11.0" > runtime.txt

# Actualizar requirements.txt
echo "dj-database-url==2.1.0" >> requirements.txt
```

### Configuración de Heroku

```bash
# Login y crear app
heroku login
heroku create tu-app-canal-denuncias

# Configurar variables de entorno
heroku config:set SECRET_KEY=tu-clave-secreta
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=tu-app-canal-denuncias.herokuapp.com

# Agregar PostgreSQL
heroku addons:create heroku-postgresql:mini

# Desplegar
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Ejecutar migraciones
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku run python manage.py collectstatic --noinput
```

---

##  Configuración Post-Despliegue

### 1. Verificación del Sistema

```bash
# Verificar servicios
sudo systemctl status nginx
sudo supervisorctl status canal_denuncias

# Verificar logs
tail -f /home/canal_denuncias/canal_denuncias/logs/gunicorn_error.log
tail -f /var/log/nginx/error.log
```

### 2. Configuración de Backup

```bash
# Script de backup de base de datos
nano /home/canal_denuncias/backup_db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/canal_denuncias/backups"
mkdir -p $BACKUP_DIR

pg_dump -h localhost -U canal_user -d canal_denuncias > $BACKUP_DIR/canal_denuncias_$DATE.sql

# Mantener solo los últimos 7 backups
find $BACKUP_DIR -name "canal_denuncias_*.sql" -mtime +7 -delete
```

```bash
# Hacer ejecutable y programar
chmod +x /home/canal_denuncias/backup_db.sh
crontab -e
# Agregar: 0 2 * * * /home/canal_denuncias/backup_db.sh
```

### 3. Monitoreo

```bash
# Instalar herramientas de monitoreo
sudo apt install htop iotop nethogs

# Configurar logrotate
sudo nano /etc/logrotate.d/canal_denuncias
```

```
/home/canal_denuncias/canal_denuncias/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 canal_denuncias canal_denuncias
    postrotate
        supervisorctl restart canal_denuncias
    endscript
}
```

### 4. Actualizaciones

```bash
# Script de actualización
nano /home/canal_denuncias/update_app.sh
```

```bash
#!/bin/bash
cd /home/canal_denuncias/canal_denuncias

# Activar entorno virtual
source venv/bin/activate

# Hacer backup antes de actualizar
./backup_db.sh

# Actualizar código
git pull origin main

# Instalar nuevas dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Reiniciar aplicación
sudo supervisorctl restart canal_denuncias

echo "Actualización completada"
```

---

##  Solución de Problemas

### Problemas Comunes

#### 1. Error 502 Bad Gateway
```bash
# Verificar que Gunicorn esté ejecutándose
sudo supervisorctl status canal_denuncias

# Verificar logs
tail -f /home/canal_denuncias/canal_denuncias/logs/gunicorn_error.log
```

#### 2. Archivos Estáticos No Cargan
```bash
# Verificar permisos
ls -la /home/canal_denuncias/canal_denuncias/staticfiles/

# Recopilar archivos estáticos
python manage.py collectstatic --clear --noinput
```

#### 3. Error de Base de Datos
```bash
sudo -u postgres psql -c "\l"

cat /home/canal_denuncias/canal_denuncias/.env | grep DATABASE
```

#### 4. Problemas de SSL
```bash
sudo certbot certificates

sudo certbot renew --dry-run
```

### Comandos Útiles

```bash
sudo systemctl restart nginx
sudo supervisorctl restart canal_denuncias

tail -f /var/log/nginx/access.log
tail -f /home/canal_denuncias/canal_denuncias/logs/supervisor.log

htop
df -h
free -m
```

---

##  Métricas y Monitoreo

### Configurar Prometheus + Grafana (Opcional)

```bash
pip install django-prometheus

INSTALLED_APPS = [
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]
```

### Alertas Básicas

```bash
nano /home/canal_denuncias/health_check.sh
```

```bash
URL="https://tu-dominio.com"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $STATUS -ne 200 ]; then
    echo "ALERTA: Sitio web no responde. Código: $STATUS" | mail -s "Canal Denuncias DOWN" admin@tu-empresa.com
fi
```

---

**Espero ya este listo para producción.**