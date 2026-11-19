# Canal de Denuncias - Sistema de Gestión de Denuncias

Un sistema web para la gestión de denuncias con proceso para la autenticación de dos factores para administradores y interfaz pública para usuarios.

## Características Principales

### Para Usuarios Públicos
- **Envío de Denuncias**: Formulario intuitivo para reportar incidencias
- **Seguimiento de Estado**: Consulta del estado usando número de folio único
- **Anonimato Opcional**: Posibilidad de enviar denuncias anónimas
- **Adjuntos**: Soporte para múltiples tipos de archivos (documentos, imágenes, videos, audio)
- **Interfaz Responsive**: Diseño adaptable a dispositivos móviles y desktop

### Para Administradores
- - **Dashboard Completo**: Vista general con estadísticas y filtros avanzados
- **Gestión de Denuncias**: Actualización de estados y respuestas
- **Historial de Cambios**: Registro completo de todas las modificaciones
- **Exportación de Datos**: Funcionalidad para exportar reportes en CSV

### Seguridad y Cumplimiento
- **Encriptación**: Todas las comunicaciones están protegidas
- **Auditoría**: Registro completo de acciones administrativas
- **Validación**: Verificación estricta de archivos y datos de entrada
- **Protección CSRF**: Prevención de ataques de falsificación de solicitudes
- **Headers de Seguridad**: Configuración completa para producción

## Requisitos del Sistema

### Requisitos Mínimos
- Python 3.12
- Django 5.2 LTS
- 512 MB RAM
- 1 GB espacio en disco
- Navegador web moderno

### Dependencias
```
Django>=5.2,<6
Pillow>=9.0
python-decouple>=3.8
django-crispy-forms>=2.0
crispy-bootstrap5>=0.7
django-ratelimit>=4.0
gunicorn>=20.0
whitenoise>=6.0
psycopg2-binary>=2.9
```

## Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd canal-denuncias
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
```bash
cp .env.example .env

SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
```

### 5. Configurar Base de Datos
```bash
python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser
```

### 6. Recopilar Archivos Estáticos (Producción)
```bash
python manage.py collectstatic
```

### 7. Ejecutar el Servidor
```bash
python manage.py runserver

gunicorn canal_denuncias.wsgi:application
```

## Configuración de Producción

### 1. Variables de Entorno de Producción
```bash
DEBUG=False
SECRET_KEY=clave-secreta-muy-segura
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
DATABASE_URL=postgresql://user:password@localhost:5432/canal_denuncias
```

### 2. Configuración de Base de Datos PostgreSQL
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'canal_denuncias',
        'USER': 'tu_usuario',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 3. Configuración de Email (2FA)
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-app-password'
```

### 4. Configuración de Servidor Web (Nginx)
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location /static/ {
        alias /path/to/canal_denuncias/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/canal_denuncias/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5. Configuración HTTPS
```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Uso del Sistema

### Para Usuarios Públicos

#### 1. Enviar una Denuncia
1. Acceder a la página principal
2. Hacer clic en "Enviar Denuncia"
3. Completar el formulario (nombre y contacto opcionales)
4. Adjuntar archivos si es necesario
5. Enviar y guardar el número de folio

#### 2. Consultar Estado
1. Hacer clic en "Consultar Estado"
2. Ingresar el número de folio
3. Ver detalles y respuestas del administrador

### Para Administradores

#### 1. Registro de Administrador
1. Acceder a `/admin/register/`
2. Completar datos personales y corporativos
3. Verificar cuenta por SMS
4. Iniciar sesión

#### 2. Gestión de Denuncias
1. Acceder al dashboard administrativo
2. Usar filtros para encontrar denuncias específicas
3. Hacer clic en una denuncia para ver detalles
4. Actualizar estado y agregar respuestas
5. Guardar cambios

#### 3. Exportación de Datos
1. En el dashboard, usar los filtros deseados
2. Hacer clic en "Exportar"
3. Descargar archivo CSV con los datos

## Seguridad

### Medidas Implementadas
- **Autenticación 2FA**: Verificación por SMS para administradores
- **Validación de Archivos**: Verificación de tipos y tamaños permitidos
- **Protección CSRF**: Tokens de seguridad en formularios
- **Headers de Seguridad**: XSS, HSTS, Content-Type protection
- **Sesiones Seguras**: Expiración automática y cookies seguras
- **Logging**: Registro completo de actividades

### Recomendaciones de Seguridad
1. **Cambiar SECRET_KEY** en producción
2. **Usar HTTPS** siempre en producción
3. **Configurar firewall** para limitar acceso
4. **Actualizar dependencias** regularmente
5. **Monitorear logs** de seguridad
6. **Backup regular** de la base de datos

## Monitoreo y Logs

### Archivos de Log
- `canal_denuncias.log`: Log principal del sistema
- Django logs: Configurados en `settings.py`

### Métricas Importantes
- Número de denuncias por día/mes
- Tiempo de respuesta promedio
- Intentos de acceso fallidos
- Uso de almacenamiento de archivos

## Solución de Problemas

### Problemas Comunes

#### Error de Migración
```bash
python manage.py migrate --fake-initial
```

#### Archivos Estáticos No Cargan
```bash
python manage.py collectstatic --clear
```

#### Error de Permisos de Archivos
```bash
chmod 755 media/
chmod 644 media/complaints/*
```

#### Problemas de SMS (2FA)
1. Verificar configuración de email en settings.py
2. Comprobar credenciales de servicio SMS
3. Revisar logs para errores específicos

### Contacto de Soporte
Para problemas técnicos o consultas:
- Email: soporte@tu-empresa.com
- Teléfono: +34 XXX XXX XXX
- Documentación: [URL de documentación]

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crear una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abrir un Pull Request

## Roadmap

### Próximas Funcionalidades
- [ ] API REST para integraciones
- [ ] Notificaciones por email automáticas
- [ ] Dashboard con gráficos avanzados
- [ ] Integración con sistemas de ticketing
- [ ] App móvil nativa
- [ ] Soporte multiidioma completo

---

**Desarrollado por Mayro Mtz para mejorar la transparencia y comunicación organizacional**
