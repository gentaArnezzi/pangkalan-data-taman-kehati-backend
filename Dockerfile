FROM python:3.12-slim

WORKDIR /app

# deps sistem minimal (libpq untuk psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ postgresql-client \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port metadata (statis saja)
EXPOSE 8000

# Pakai shell form agar $PORT diekspansi di runtime Render
CMD sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'
