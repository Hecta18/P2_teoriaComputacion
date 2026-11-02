FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

CMD ["python", "reconocer.py", "--archivo", "cadenas.txt"]
