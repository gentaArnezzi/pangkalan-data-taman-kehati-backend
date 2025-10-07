#!/bin/bash
# Test script to verify deployment configuration

echo "Checking deployment configuration files..."

# Check if required files exist
files=(
    "Procfile"
    "Dockerfile" 
    "requirements.txt"
    "app/main.py"
    "RENDER_ENV.md"
    "RENDER_DEPLOYMENT_GUIDE.md"
    "docker-compose.render.yml"
    "render.yaml"
)

echo "Verifying required files:"
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
        exit 1
    fi
done

echo ""
echo "Checking Procfile content..."
if grep -q "uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-8000}" Procfile; then
    echo "✓ Procfile has correct command"
else
    echo "✗ Procfile command is incorrect"
    exit 1
fi

echo ""
echo "Checking Dockerfile content..."
if grep -q "EXPOSE \$PORT" Dockerfile && grep -q "CMD \[\"uvicorn\"" Dockerfile; then
    echo "✓ Dockerfile has correct EXPOSE and CMD"
else
    echo "✗ Dockerfile EXPOSE or CMD is incorrect"
    exit 1
fi

echo ""
echo "Checking app structure..."
if [ -f "app/main.py" ] && grep -q "FastAPI" app/main.py; then
    echo "✓ FastAPI application found"
else
    echo "✗ FastAPI application not found or incorrect"
    exit 1
fi

echo ""
echo "All checks passed! Your deployment configuration is ready for Render."
echo ""
echo "Next steps:"
echo "1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)"
echo "2. Create a PostgreSQL database on Render"
echo "3. Follow the instructions in RENDER_DEPLOYMENT_GUIDE.md"
echo "4. Use the environment variables listed in RENDER_ENV.md"