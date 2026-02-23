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

Copy this into a new file called '.env'

```
SECRET_KEY="copy_key_here"
DEBUG="False"
DATABASE_URL="postgres://tadauser:tadapw@db:5432/tada"
```

Go to https://djecrety.ir/ and create a new Django key

Replace `"copy_key_here"` with your new key (in quotes)

### 5. Docker Containers

Run this

```
docker compose build
docker compose up -d
```

You should see your docker containers in VS Code and in your Docker Desktop

### 6. Run migrations

This will open a shell inside the container

```
docker exec -it tada-web-1 sh
python manage.py makemigrations candidates
python manage.py migrate
```

### 7. Create sample data

Run this

```
python manage.py create_cand_data
```

And then exit the container shell

```
exit
```

### 8. Test

Visit localhost:8000 in your browser to see if it's working

# Notes

You will no longer need the venv file, the container has its own venv

Anytime you need to refresh the webserver, run this

```
docker compose up -d --build
```

Edit HTML files in TADA\candidates\templates

Useful website: https://www.w3schools.com/django/index.php

Make sure DEBUG is false and ALLOWED_HOSTS is configured bfore deploying!