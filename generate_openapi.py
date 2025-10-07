import json
from main import app

# Generate OpenAPI schema
openapi_schema = app.openapi()

# Write to file
with open("openapi.json", "w") as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI documentation regenerated successfully!")