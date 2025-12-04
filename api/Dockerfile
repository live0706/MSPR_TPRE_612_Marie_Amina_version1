FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Exposition du port
EXPOSE 8000

# Lancement du serveur
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]