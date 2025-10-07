import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.artikel import create_artikel, get_artikel, get_artikels
from app.models import Artikel as ArtikelModel
from app.schemas.artikel import ArtikelCreate
from uuid import UUID
import uuid

@pytest.mark.asyncio
async def test_create_artikel():
    """Test creating an article via CRUD layer."""
    # Mock the database session
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Create the mock return value for execute().scalars().first()
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None  # No existing article with this slug
    
    # Mock the execute method to return the mock result when called
    with patch('app.crud.artikel.select') as mock_select:
        mock_db.execute.return_value = mock_result
        
        # Create test data
        test_author_id = uuid.uuid4()
        artikel_data = ArtikelCreate(
            judul="Test Artikel",
            ringkasan="Test ringkasan",
            konten="Test konten",
            author_id=test_author_id,
            taman_kehati_id=1
        )
        
        # Call the CRUD function
        result = await create_artikel(
            db=mock_db,
            artikel=artikel_data,
            current_user_id=test_author_id
        )
        
        # Verify the database interaction
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        
        # Verify that the created object has the expected properties
        assert isinstance(result, ArtikelModel)
        assert result.judul == "Test Artikel"
        assert result.author_id == test_author_id
        assert result.taman_kehati_id == 1


@pytest.mark.asyncio
async def test_get_artikel():
    """Test getting an article by ID."""
    # Mock the database session and result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_artikel = MagicMock(spec=ArtikelModel)
    mock_artikel.id = 1
    mock_artikel.judul = "Test Artikel"
    mock_result.scalars().first.return_value = mock_artikel
    
    mock_db.execute.return_value = mock_result
    
    # Call the CRUD function
    result = await get_artikel(db=mock_db, artikel_id=1)
    
    # Verify the database query was called
    assert mock_db.execute.called
    
    # Verify result
    assert result == mock_artikel


@pytest.mark.asyncio 
async def test_get_artikels():
    """Test getting multiple articles."""
    # Mock the database session and result
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_artikel1 = MagicMock(spec=ArtikelModel)
    mock_artikel1.id = 1
    mock_artikel1.judul = "Test Artikel 1"
    
    mock_artikel2 = MagicMock(spec=ArtikelModel)
    mock_artikel2.id = 2
    mock_artikel2.judul = "Test Artikel 2"
    
    mock_result.scalars().all.return_value = [mock_artikel1, mock_artikel2]
    mock_db.execute.return_value = mock_result
    
    # Call the CRUD function
    results = await get_artikels(db=mock_db, skip=0, limit=10)
    
    # Verify the database query was called
    assert mock_db.execute.called
    
    # Verify results
    assert len(results) == 2
    assert results[0].judul == "Test Artikel 1"
    assert results[1].judul == "Test Artikel 2"