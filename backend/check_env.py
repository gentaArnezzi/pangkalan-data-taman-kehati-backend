#!/usr/bin/env python3
import os
from dotenv import dotenv_values

# Load only from .env file, not system environment variables
env_values = dotenv_values(".env")
print("From .env file:")
print("DATABASE_URL:", env_values.get("DATABASE_URL"))
print("ASYNC_DATABASE_URL:", env_values.get("ASYNC_DATABASE_URL"))
print()

# Load using load_dotenv and check
from dotenv import load_dotenv
load_dotenv(override=True)  # Override system variables with .env

print("After load_dotenv with override:")
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
print("ASYNC_DATABASE_URL:", os.getenv("ASYNC_DATABASE_URL"))