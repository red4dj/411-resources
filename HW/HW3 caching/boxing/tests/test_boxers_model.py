import time

import pytest

from boxing.models.ring_model import RingModel
from boxing.models.boxers_model import Boxers

@pytest.fixture
def ring_model():
    """Fixture to provide a new instance of RingModel for each test."""
    return RingModel()

@pytest.fixture
def sample_boxer1(session):
    boxer = Boxers(name="Muhammad Ali", weight=210, height=191, reach=78, age=32)
    session.add(boxer)
    session.commit()
    return boxer

@pytest.fixture
def sample_boxer2(session):
    boxer = Boxers(name="Mike Tyson", weight=220, height=178, reach=71, age=24)
    session.add(boxer)
    session.commit()
    return boxer

@pytest.fixture
def sample_boxers(sample_boxer1, sample_boxer2):
    return [sample_boxer1, sample_boxer2]

# --- Ring Clear ---

def test_clear_ring(ring_model):
    """Test that clear_ring empties the ring."""
    ring_model.ring = [1, 2]
    ring_model.clear_ring()
    assert len(ring_model.ring) == 0

def test_clear_ring_empty(ring_model, caplog):
    """Test that clear_ring logs a warning when already empty."""
    with caplog.at_level("WARNING"):
        ring_model.clear_ring()
    assert len(ring_model.ring) == 0
    assert "Attempted to clear an empty ring." in caplog.text

def test_get_boxers_empty(ring_model, caplog):
    """Test get_boxers logs when empty."""
    with caplog.at_level("WARNING"):
        boxers = ring_model.get_boxers()
    assert boxers == []
    assert "Retrieving boxers from an empty ring." in caplog.text

def test_get_boxers_with_data(app, ring_model, sample_boxers):
    """Test get_boxers with two sample boxers."""
    ring_model.ring.extend([b.id for b in sample_boxers])
    boxers = ring_model.get_boxers()
    assert boxers == sample_boxers

def test_get_boxers_uses_cache(ring_model, sample_boxer1, mocker):
    ring_model.ring.append(sample_boxer1.id)
    ring_model._boxer_cache[sample_boxer1.id] = sample_boxer1
    ring_model._ttl[sample_boxer1.id] = time.time() + 100
    mock_get = mocker.patch("boxing.models.ring_model.Boxers.get_boxer_by_id")
    boxers = ring_model.get_boxers()
    assert boxers[0] == sample_boxer1
    mock_get.assert_not_called()

def test_get_boxers_refreshes_on_expired_ttl(ring_model, sample_boxer1, mocker):
    ring_model.ring.append(sample_boxer1.id)
    ring_model._boxer_cache[sample_boxer1.id] = mocker.Mock()
    ring_model._ttl[sample_boxer1.id] = time.time() - 1
    mock_get = mocker.patch("boxing.models.ring_model.Boxers.get_boxer_by_id", return_value=sample_boxer1)
    boxers = ring_model.get_boxers()
    assert boxers[0] == sample_boxer1
    mock_get.assert_called_once_with(sample_boxer1.id)

def test_cache_populated_on_get_boxers(ring_model, sample_boxer1, mocker):
    mock_get = mocker.patch("boxing.models.ring_model.Boxers.get_boxer_by_id", return_value=sample_boxer1)
    ring_model.ring.append(sample_boxer1.id)
    boxers = ring_model.get_boxers()
    assert sample_boxer1.id in ring_model._boxer_cache
    assert sample_boxer1.id in ring_model._ttl
    assert boxers[0] == sample_boxer1

def test_enter_ring(ring_model, sample_boxers, app):
    ring_model.enter_ring(sample_boxers[0].id)
    assert ring_model.ring == [sample_boxers[0].id]
    ring_model.enter_ring(sample_boxers[1].id)
    assert ring_model.ring == [sample_boxers[0].id, sample_boxers[1].id]

def test_enter_ring_full(ring_model):
    ring_model.ring = [1, 2]
    with pytest.raises(ValueError, match="Ring is full"):
        ring_model.enter_ring(3)


# --- Fight Logic ---

def test_get_fighting_skill(ring_model, sample_boxers):
    expected_1 = 210 * 12 + (78 / 10)
    expected_2 = 220 * 10 + (71 / 10) - 1
    assert ring_model.get_fighting_skill(sample_boxers[0]) == expected_1
    assert ring_model.get_fighting_skill(sample_boxers[1]) == expected_2

def test_fight(ring_model, sample_boxers, caplog, mocker):
    ring_model.ring.extend(sample_boxers)
    mocker.patch("boxing.models.ring_model.RingModel.get_fighting_skill", side_effect=[2526.8, 2206.1])
    mocker.patch("boxing.models.ring_model.get_random", return_value=0.42)
    mocker.patch("boxing.models.ring_model.RingModel.get_boxers", return_value=sample_boxers)
    mock_update = mocker.patch("boxing.models.ring_model.Boxers.update_stats")
    winner = ring_model.fight()
    assert winner == "Muhammad Ali"
    mock_update.assert_any_call("win")
    mock_update.assert_any_call("loss")
    assert ring_model.ring == []

def test_fight_with_empty_ring(ring_model):
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()

def test_fight_with_one_boxer(ring_model, sample_boxer1):
    ring_model.ring.append(sample_boxer1)
    with pytest.raises(ValueError, match="There must be two boxers to start a fight."):
        ring_model.fight()

def test_clear_cache(ring_model, sample_boxer1):
    ring_model._boxer_cache[sample_boxer1.id] = sample_boxer1
    ring_model._ttl[sample_boxer1.id] = time.time() + 100
    ring_model.clear_cache()
    assert ring_model._boxer_cache == {}
    assert ring_model._ttl == {}
