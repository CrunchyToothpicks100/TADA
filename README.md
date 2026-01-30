## Setup

If you don't have python, install python 3.14.2 and add it to your PATH

After cloning the repo, open a terminal in the project directory and run these

```powershell
python -m venv .venv
.\.venv\scripts\activate
pip install -r requirements.txt
```

Run the project

```powershell
python manage.py runserver
```

Visit localhost:8000 in your browser to see if it's working

Edit HTML files in TADA\candidates\templates