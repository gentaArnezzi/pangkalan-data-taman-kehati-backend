# Taman Kehati Backend

FastAPI backend for Taman Kehati project.

## Setup

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:

   ```bash
   # On macOS/Linux:
   source .venv/bin/activate

   # On Windows:
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies (optional):

   ```bash
   pip install -r requirements-dev.txt
   ```

5. Set up environment variables by copying `.env.example` to `.env` and updating values as needed.

6. Initialize the database:
   ```bash
   python init_db.py
   ```

## Running the application

### Method 1: Using Makefile (Recommended)

The project includes a Makefile with convenient commands:

- Start the development server:

  ```bash
  make dev
  ```

- For production:
  ```bash
  make run
  ```

### Method 2: Direct Uvicorn Command

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Using Docker (if available)

```bash
docker-compose up --build
```

## Development Commands

- Run tests:

  ```bash
  make test
  ```

- Lint and format code:

  ```bash
  make lint
  ```

- Run database migrations:

  ```bash
  make migrate
  ```

- Seed database (initialize with sample data):

  ```bash
  make seed
  ```

- Generate a new database migration:

  ```bash
  make migrate-make msg="migration message"
  ```

- Install dependencies:

  ```bash
  make install
  ```

- Install development dependencies:

  ```bash
  make install-dev
  ```

- Clean cache files:

  ```bash
  make clean
  ```

- Full setup:
  ```bash
  make setup
  ```

## API Documentation

Once the application is running, you can access:

- Interactive API documentation at `http://localhost:8000/docs`
- Alternative API documentation at `http://localhost:8000/redoc`
- OpenAPI schema at `http://localhost:8000/openapi.json`
