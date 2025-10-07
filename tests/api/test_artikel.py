import pytest
from httpx import AsyncClient
from app.main import app
from app.database import get_db
import asyncio

# Simple tests to verify the API endpoints exist
@pytest.mark.asyncio
async def test_artikel_endpoints_exist():
    """Test that artikel endpoints are available."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Test list endpoint
        response = await ac.get("/api/artikel/")
        # Should return 401 since auth is required (or 422 for validation)
        assert response.status_code in [401, 422, 200]
        
        # Test non-existing slug
        response = await ac.get("/api/artikel/slug/invalid-slug")
        assert response.status_code in [401, 404, 422]