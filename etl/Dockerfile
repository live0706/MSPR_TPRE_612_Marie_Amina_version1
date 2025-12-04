# Image légère
FROM python:3.11-slim

# Optimisations Python pour Docker (Logs en temps réel + Pas de fichiers .pyc)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Commande par défaut
CMD ["python", "main_etl.py"]