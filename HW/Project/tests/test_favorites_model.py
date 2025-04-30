import time

import pytest

from ducks.models.favorites_model import FavoritesModel
from ducks.models.ducks_model import Ducks
from ducks.utils.api_utils import get_duck

@pytest.fixture
def favorites_model():
    """Fixture to provide a new instance of FavoritesModel for each test."""
    return FavoritesModel()

@pytest.fixture
def sample_duck1(session):
    duck_url = get_duck()
    duck = Ducks(url=duck_url)
    session.add(duck)
    session.commit()
    return duck

@pytest.fixture
def sample_duck2(session):
    duck_url = get_duck()
    duck = Ducks(url=duck_url)
    session.add(duck)
    session.commit()
    return duck

@pytest.fixture
def sample_ducks(sample_duck1, sample_duck2):
    return [sample_duck1, sample_duck2]

# --- Favorites Add/Remove ---

def test_add_duck_to_favorites(favorites_model, sample_duck1, mocker):
    """Test adding a duck to favorites."""
    mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id", return_value=sample_duck1)
    favorites_model.add_duck_to_favorites(1)
    assert len(favorites_model.favorites) == 1
    assert favorites_model.favorites[0] == 1


def test_add_duplicate_duck_to_favorites(favorites_model, sample_duck1, mocker):
    """Test error when adding a duplicate duck to favorites by ID."""
    mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id", side_effect=[sample_duck1] * 2)
    favorites_model.add_duck_to_favorites(1)
    with pytest.raises(ValueError, match="Duck with ID 1 already exists in favorites"):
        favorites_model.add_duck_to_favorites(1)


def test_remove_duck_from_favorites_by_duck_id(favorites_model, mocker):
    """Test removing a duck from favorites by duck_id."""
    mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id", return_value=sample_duck1)

    favorites_model.favorites = [1,2]

    favorites_model.remove_duck_by_duck_id(1)
    assert len(favorites_model.favorites) == 1, f"Expected 1 duck, but got {len(favorites_model.favorites)}"
    assert favorites_model.favorites[0] == 2, "Expected duck with id 2 to remain"

# --- Favorites Clear ---

def test_clear_favorites(favorites_model):
    """Test that clear_favorites empties favorites."""
    favorites_model.favorites = [1, 2]
    favorites_model.clear_favorites()
    assert len(favorites_model.ring) == 0

def test_clear_favorites_empty(favorites_model, caplog):
    """Test that clear_favorites logs a warning when already empty."""
    with caplog.at_level("WARNING"):
        favorites_model.clear_favorites()
    assert len(favorites_model.favorites) == 0
    assert "Attempted to clear an empty favorites list." in caplog.text


# --- Favorites Get ---

def test_get_duck_by_duck_id(favorites_model, sample_duck1):
    """Test get_duck_by_duck_id."""
    favorites_model.favorites = [1, 2]
    duck = favorites_model.get_duck_by_duck_id(1)
    assert duck == sample_duck1

def test_get_duck_by_duck_id_not_found(favorites_model):
    """Test get_duck_by_duck_id raises ValueError when duck not found."""
    favorites_model.favorites = [1, 2]
    with pytest.raises(ValueError, match="Invalid duck ID"):
        favorites_model.get_duck_by_duck_id(3)

def test_get_duck_by_duck_id_empty(favorites_model):
    """Test get_duck_by_duck_id raises ValueError when favorites is empty."""
    with pytest.raises(ValueError, match="Favorites list is empty"):
        favorites_model.get_duck_by_duck_id(1)

def test_get_ducks_empty(favorites_model, caplog):
    """Test get_ducks logs when empty."""
    with caplog.at_level("WARNING"):
        ducks = favorites_model.get_ducks()
    assert ducks == []
    assert "Attempted to retrieve ducks from an empty favorites list." in caplog.text

def test_get_ducks_with_data(app, favorites_model, sample_ducks):
    """Test get_ducks with two sample ducks."""
    favorites_model.favorites.extend([b.id for b in sample_ducks])
    ducks = favorites_model.get_ducks()
    assert ducks == sample_ducks

def test_get_ducks_uses_cache(favorites_model, sample_duck1, mocker):
    favorites_model.favorites.append(sample_duck1.id)
    favorites_model._ducks_cache[sample_duck1.id] = sample_duck1
    favorites_model._ttl[sample_duck1.id] = time.time() + 100
    mock_get = mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id")
    ducks = favorites_model.get_ducks()
    assert ducks[0] == sample_duck1
    mock_get.assert_not_called()

def test_get_ducks_refreshes_on_expired_ttl(favorites_model, sample_duck1, mocker):
    favorites_model.favorites.append(sample_duck1.id)
    favorites_model._ducks_cache[sample_duck1.id] = mocker.Mock()
    favorites_model._ttl[sample_duck1.id] = time.time() - 1
    mock_get = mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id", return_value=sample_duck1)
    ducks = favorites_model.get_ducks()
    assert ducks[0] == sample_duck1
    mock_get.assert_called_once_with(sample_duck1.id)

def test_cache_populated_on_get_ducks(favorites_model, sample_duck1, mocker):
    mock_get = mocker.patch("ducks.models.favorites_model.Ducks.get_duck_by_id", return_value=sample_duck1)
    favorites_model.favorites.append(sample_duck1.id)
    ducks = favorites_model.get_ducks()
    assert sample_duck1.id in favorites_model._ducks_cache
    assert sample_duck1.id in favorites_model._ttl
    assert ducks[0] == sample_duck1

def test_clear_cache(favorites_model, sample_duck1):
    favorites_model._ducks_cache[sample_duck1.id] = sample_duck1
    favorites_model._ttl[sample_duck1.id] = time.time() + 100
    favorites_model.clear_cache()
    assert favorites_model._ducks_cache == {}
    assert favorites_model._ttl == {}
