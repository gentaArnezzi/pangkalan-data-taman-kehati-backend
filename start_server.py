#!/usr/bin/env python3
"""
Start script for Taman Kehati API with proper PORT handling for deployment environments.
"""
import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False  # Disable reload in production
    )