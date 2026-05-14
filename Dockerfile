FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=myproject.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

ENTRYPOINT ["sh", "-c", "python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:8000 myproject.wsgi:application"]
