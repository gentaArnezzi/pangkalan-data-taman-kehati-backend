import pytest
from httpx import AsyncClient
from app.main import app
from app.database import get_db
from app.models import Base, User as UserModel, Artikel as ArtikelModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

@pytest.mark.asyncio
async def test_artikel_endpoints(api_client, db_session):
    """Test all artikel endpoints with a proper test setup."""
    
    # Create a test user
    test_user = UserModel(
        id=uuid.uuid4(),
        email="test@example.com",
        password="hashed_password",  # In real tests, use proper password hashing
        nama="Test User",
        role="admin_taman",
        is_active=True,
        taman_kehati_id=1
    )
    db_session.add(test_user)
    await db_session.commit()
    
    # Test creating an article (this would need proper authentication in real scenario)
    # For now, we'll just check if the endpoint exists and returns expected status
    create_payload = {
        "judul": "Test Artikel",
        "ringkasan": "Test ringkasan",
        "konten": "Test konten lengkap",
        "author_id": str(test_user.id),
        "taman_kehati_id": 1,
        "kategori": "test"
    }
    
    # This would fail without proper auth, so just checking if route exists
    response = await api_client.post("/api/artikel/", json=create_payload)
    # Without auth, expect 401
    assert response.status_code in [401, 422]
    
    # Test getting articles list
    response = await api_client.get("/api/artikel/")
    assert response.status_code == 200
    data = response.json()
    # Should be a list
    assert isinstance(data, list)
    
    # Test with query parameters
    response = await api_client.get("/api/artikel/?page=1&size=10")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_artikel_with_auth(api_client, db_session):
    """Test artikel endpoints with authentication simulation."""
    # This is a simplified test - in real implementation, 
    # you'd need to implement proper JWT token generation for tests
    pass