# Use a slim and secure base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# The EXPOSE instruction is documentation for developers and tools.
# Render does not use it, but it's good practice to declare the port your app intends to use.
# We use a variable that can be overridden at build time if needed.
ARG PORT=8000
EXPOSE $PORT

# Run the web server using a shell to expand the $PORT environment variable.
# Render dynamically assigns a port and sets it in the $PORT env var at runtime.
# Using "sh -c" ensures that $PORT is correctly interpreted.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
