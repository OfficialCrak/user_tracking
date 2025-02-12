FROM python:3.10-slim
WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y libpq-dev gcc netcat-openbsd

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /app/
COPY wait-for-it.sh /app/

RUN chmod +x /app/entrypoint.sh /app/wait-for-it.sh


COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]