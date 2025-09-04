FROM python:3.11

WORKDIR /app

# System dependencies (needed for mysqlclient)
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run migrations on container start (optional)
CMD ["gunicorn", "mw_es.wsgi:application", "--bind", "0.0.0.0:8000"]