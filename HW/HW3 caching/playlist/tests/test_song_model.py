import pytest

from playlist.models.song_model import Songs


# --- Fixtures ---

@pytest.fixture
def song_beatles(session):
    """Fixture for The Beatles - Hey Jude."""
    song = Songs(artist="The Beatles", title="Hey Jude", year=1968, genre="Rock", duration=431)
    session.add(song)
    session.commit()
    return song

@pytest.fixture
def song_nirvana(session):
    """Fixture for Nirvana - Smells Like Teen Spirit."""
    song = Songs(artist="Nirvana", title="Smells Like Teen Spirit", year=1991, genre="Grunge", duration=301)
    session.add(song)
    session.commit()
    return song


# --- Create Song ---

def test_create_song(session):
    """Test creating a new song."""
    Songs.create_song("Queen", "Bohemian Rhapsody", 1975, "Rock", 354)
    song = session.query(Songs).filter_by(title="Bohemian Rhapsody").first()
    assert song is not None
    assert song.artist == "Queen"


def test_create_duplicate_song(session, song_beatles):
    """Test creating a song with a duplicate artist/title/year."""
    with pytest.raises(ValueError, match="already exists"):
        Songs.create_song("The Beatles", "Hey Jude", 1968, "Rock", 431)


@pytest.mark.parametrize("artist, title, year, genre, duration", [
    ("", "Valid Title", 2000, "Pop", 180),
    ("Valid Artist", "", 2000, "Pop", 180),
    ("Valid Artist", "Valid Title", 1899, "Pop", 180),
    ("Valid Artist", "Valid Title", 2000, "", 180),
    ("Valid Artist", "Valid Title", 2000, "Pop", 0),
])
def test_create_song_invalid_data(artist, title, year, genre, duration):
    """Test validation errors when creating a song."""
    with pytest.raises(ValueError):
        Songs.create_song(artist, title, year, genre, duration)


# --- Get Song ---

def test_get_song_by_id(song_beatles):
    """Test fetching a song by ID."""
    fetched = Songs.get_song_by_id(song_beatles.id)
    assert fetched.title == "Hey Jude"

def test_get_song_by_id_not_found(app):
    """Test error when fetching nonexistent song by ID."""
    with pytest.raises(ValueError, match="not found"):
        Songs.get_song_by_id(999)


def test_get_song_by_compound_key(song_nirvana):
    """Test fetching a song by compound key."""
    song = Songs.get_song_by_compound_key("Nirvana", "Smells Like Teen Spirit", 1991)
    assert song.genre == "Grunge"

def test_get_song_by_compound_key_not_found(app):
    """Test error when fetching nonexistent song by compound key."""
    with pytest.raises(ValueError, match="not found"):
        Songs.get_song_by_compound_key("Ghost", "Invisible Song", 2024)


# --- Delete Song ---

def test_delete_song_by_id(session, song_beatles):
    """Test deleting a song by ID."""
    Songs.delete_song(song_beatles.id)
    assert session.query(Songs).get(song_beatles.id) is None

def test_delete_song_not_found(app):
    """Test deleting a non-existent song by ID."""
    with pytest.raises(ValueError, match="not found"):
        Songs.delete_song(999)


# --- Play Count ---

def test_update_play_count(session, song_nirvana):
    """Test incrementing play count."""
    assert song_nirvana.play_count == 0
    song_nirvana.update_play_count()
    session.refresh(song_nirvana)
    assert song_nirvana.play_count == 1


# --- Get All Songs ---

def test_get_all_songs(session, song_beatles, song_nirvana):
    """Test retrieving all songs."""
    songs = Songs.get_all_songs()
    assert len(songs) == 2

def test_get_all_songs_sorted(session, song_beatles, song_nirvana):
    """Test retrieving songs sorted by play count."""
    song_nirvana.play_count = 5
    song_beatles.play_count = 3
    session.commit()
    sorted_songs = Songs.get_all_songs(sort_by_play_count=True)
    assert sorted_songs[0]["title"] == "Smells Like Teen Spirit"


# --- Random Song ---

def test_get_random_song(session, song_beatles, song_nirvana):
    """Test getting a random song as a dictionary with expected fields."""
    song = Songs.get_random_song()

    assert isinstance(song, dict), "Expected a dictionary representing a song"
    assert set(song.keys()) == {"id", "artist", "title", "year", "genre", "duration", "play_count"}, \
        f"Unexpected keys in song dict: {song.keys()}"
    assert isinstance(song["title"], str) and song["title"], "Song title should be a non-empty string"
    assert isinstance(song["play_count"], int), "Play count should be an integer"


def test_get_random_song_empty(session):
    """Test error when no songs exist."""
    Songs.query.delete()
    session.commit()
    with pytest.raises(ValueError, match="empty"):
        Songs.get_random_song()
