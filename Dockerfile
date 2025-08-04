# Dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collect static files (optional)
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "projectname.wsgi:application", "--bind", "0.0.0.0:8000"]
