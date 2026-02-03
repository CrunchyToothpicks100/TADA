## Setup

1. If you don't have python, install python 3.14.2 and add it to your PATH

2. After cloning the repo, open a terminal in the project directory and run these

```powershell
py -m venv .venv
.\.venv\scripts\activate
pip install -r requirements.txt
```

3. Generate new secret key

```powershell
py -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

4. Create a new file, name it '.env', and add

```python
SECRET_KEY="your_new_key"
DEBUG="False"
```

5. Run migrations (you must do this every time the model is updated)

```powershell
py manage.py makemigrations candidates
py manage.py migrate
```

6. Create sample data

```poowershell
py manage.py create_cand_data
```

6. Run the project

```powershell
python manage.py runserver
```

7. Visit localhost:8000 in your browser to see if it's working

Edit HTML files in TADA\candidates\templates

Useful website: https://www.w3schools.com/django/index.php

NOTES:
Make sure DEBUG is false and ALLOWED_HOSTS is configured bfore deploying!