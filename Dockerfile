FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=myproject.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || echo "No static files to collect or STATIC_ROOT not set"

EXPOSE 8000

# Run migrations and start server automatically
CMD python manage.py migrate --noinput && \
    gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application