# Use official Python image
FROM python:3.12-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install vim for easier debugging
RUN apt-get update \
    && apt-get install -y --no-install-recommends vim \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install --upgrade pip
RUN pip install poetry

# Copy dependency files first
COPY pyproject.toml poetry.lock ./

# Install dependencies with Poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

# Copy project files
COPY . .

# Use 'pymg' as an alias for 'python manage.py'
RUN echo "pymg() { python manage.py \"\$@\"; }" >> /root/.bashrc
RUN echo "echo 'BASHRC loaded'" >> /root/.bashrc

# Expose port
EXPOSE 8000

# Run server
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
