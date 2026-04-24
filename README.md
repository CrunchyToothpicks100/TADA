












# Setup

### 1. Download Docker Desktop

https://www.docker.com/products/docker-desktop/

### 2. Download Extensions (optional)

Download 'Container Tools' and 'Docker' from your VS Code extensions

### 3. Clone repository

Open a terminal and run these

```
git clone https://github.com/CrunchyToothpicks100/TADA/
cd TADA
```

### 4. Environment variables

Copy `.env.example` into a new file called `.env`, then replace the secret and
database password values.

```
SECRET_KEY="copy_key_here"
DEBUG="False"
ALLOWED_HOSTS="tada.fbstudios.com,localhost,127.0.0.1,192.168.22.170"
CSRF_TRUSTED_ORIGINS="https://tada.fbstudios.com"
SECURE_SSL_REDIRECT="True"
SECURE_HSTS_SECONDS="31536000"
SECURE_HSTS_INCLUDE_SUBDOMAINS="False"
SECURE_HSTS_PRELOAD="False"
SESSION_COOKIE_SECURE="True"
CSRF_COOKIE_SECURE="True"
TADA_WEB_BIND="127.0.0.1"
TADA_WEB_PORT="8017"
POSTGRES_DB="tada"
POSTGRES_USER="tadauser"
POSTGRES_PASSWORD="copy_strong_password_here"
```

Go to https://djecrety.ir/ and create a new Django key

Replace `"copy_key_here"` with your new key (in quotes)

### 5. Docker Containers

Run this

```
docker compose build
docker compose up -d
```

The web container runs `collectstatic`, applies migrations, and starts gunicorn.
By default, it binds to `127.0.0.1:8017` so nginx on the same server can proxy to
it without exposing the app directly or colliding with common host ports.

### 6. Create sample data

Run this

```
docker compose exec web python manage.py create_sample_data
```

### 7. Test

Visit localhost:8017 in your browser to see if it's working

# Notes

You will no longer need the venv file, the container has its own venv

Anytime you need to refresh the webserver, run this

```
docker compose up -d --build
```

Edit HTML files in TADA\candidates\templates

Useful website: https://www.w3schools.com/django/index.php

Make sure DEBUG is false and ALLOWED_HOSTS is configured before deploying!
