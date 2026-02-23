FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=myproject.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project code
COPY . .

# Optional: collect static files if you use them
RUN python manage.py collectstatic --noinput 2>/dev/null || echo "No static files or STATIC_ROOT not set"

EXPOSE 8000

# ENTRYPOINT ensures migrations run before starting Gunicorn
ENTRYPOINT ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application"]