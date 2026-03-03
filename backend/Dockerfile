FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Herramientas de compilación (por si alguna lib lo requiere)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalarlos
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código de la app
COPY . /app

# Puerto que usará FastAPI/Uvicorn
EXPOSE 8080

# Comando de arranque
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
