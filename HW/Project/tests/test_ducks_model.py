import pytest


from ducks.models.ducks_model import Ducks
from ducks.utils.logger import configure_logger
from ducks.utils.api_utils import get_duck
from ducks.utils.api_utils import get_quack


# --- Fixtures ---

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


# --- Create Duck ---

def test_create_duck_random(session):
    """Test creating a new random duck."""
    Ducks.create_duck_random()
    duck = session.query(Ducks).filter_by(id=1).first()
    assert duck is not None
    assert duck.url is not None

def test_create_duck_with_url(session):
    """Test creating a new duck with a specific URL."""
    url = "https://example.com/duck.jpg"
    Ducks.create_duck_with_url(url)
    duck = session.query(Ducks).filter_by(url=url).first()
    assert duck is not None
    assert duck.url == url


def test_create_duplicate_duck(session, sample_duck1):
    """Test creating a duck with a duplicate artist/title/year."""
    with pytest.raises(ValueError, match=f"Duck already exists: {sample_duck1.url.strip()}"):
        Ducks.create_duck_with_url(url=sample_duck1.url)


def test_create_duck_invalid_data(session):
    """Test validation errors when creating a duck."""
    with pytest.raises(ValueError):
        Ducks.create_duck_with_url("")


# --- Get Duck ---

def test_get_duck_by_id(sample_duck1):
    """Test fetching a duck by ID."""
    fetched = Ducks.get_duck_by_id(sample_duck1.id)
    assert fetched.url == sample_duck1.url

def test_get_duck_by_id_not_found(app):
    """Test error when fetching nonexistent duck by ID."""
    with pytest.raises(ValueError, match="Duck with ID 999 not found."):
        Ducks.get_duck_by_id(999)


# --- Delete Duck ---

def test_delete_duck(session, sample_duck1):
    """Test deleting a duck by ID."""
    Ducks.delete_duck(sample_duck1.id)
    assert session.query(Ducks).get(sample_duck1.id) is None

def test_delete_duck_not_found(app):
    """Test deleting a non-existent duck by ID."""
    with pytest.raises(ValueError, match="Duck with ID 999 not found."):
        Ducks.delete_duck(999)


# --- Quack ---

def test_make_duck_quack():
    """Test quack function."""
    quack = Ducks.make_duck_quack()
    assert quack is not None
    assert isinstance(quack, str)
    assert len(quack) > 0



