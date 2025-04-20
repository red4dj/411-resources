import pytest

from playlist.models.playlist_model import PlaylistModel
from playlist.models.song_model import Songs


@pytest.fixture()
def playlist_model():
    """Fixture to provide a new instance of PlaylistModel for each test."""
    return PlaylistModel()

"""Fixtures providing sample songs for the tests."""
@pytest.fixture
def song_beatles(session):
    """Fixture for a Beatles song."""
    song = Songs(
        artist="The Beatles",
        title="Come Together",
        year=1969,
        genre="Rock",
        duration=259
    )
    session.add(song)
    session.commit()
    return song

@pytest.fixture
def song_nirvana(session):
    """Fixture for a Nirvana song."""
    song = Songs(
        artist="Nirvana",
        title="Smells Like Teen Spirit",
        year=1991,
        genre="Grunge",
        duration=301
    )
    session.add(song)
    session.commit()
    return song

@pytest.fixture
def sample_playlist(song_beatles, song_nirvana):
    """Fixture for a sample playlist."""
    return [song_beatles, song_nirvana]

##################################################
# Add / Remove Song Management Test Cases
##################################################


def test_add_song_to_playlist(playlist_model, song_beatles, mocker):
    """Test adding a song to the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_beatles)
    playlist_model.add_song_to_playlist(1)
    assert len(playlist_model.playlist) == 1
    assert playlist_model.playlist[0] == 1


def test_add_duplicate_song_to_playlist(playlist_model, song_beatles, mocker):
    """Test error when adding a duplicate song to the playlist by ID."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=[song_beatles] * 2)
    playlist_model.add_song_to_playlist(1)
    with pytest.raises(ValueError, match="Song with ID 1 already exists in the playlist"):
        playlist_model.add_song_to_playlist(1)


def test_remove_song_from_playlist_by_song_id(playlist_model, mocker):
    """Test removing a song from the playlist by song_id."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_beatles)

    playlist_model.playlist = [1,2]

    playlist_model.remove_song_by_song_id(1)
    assert len(playlist_model.playlist) == 1, f"Expected 1 song, but got {len(playlist_model.playlist)}"
    assert playlist_model.playlist[0] == 2, "Expected song with id 2 to remain"


def test_remove_song_by_track_number(playlist_model):
    """Test removing a song from the playlist by track number."""
    playlist_model.playlist = [1,2]
    assert len(playlist_model.playlist) == 2

    playlist_model.remove_song_by_track_number(1)
    assert len(playlist_model.playlist) == 1, f"Expected 1 song, but got {len(playlist_model.playlist)}"
    assert playlist_model.playlist[0] == 2, "Expected song with id 2 to remain"


def test_clear_playlist(playlist_model):
    """Test clearing the entire playlist."""
    playlist_model.playlist.append(1)

    playlist_model.clear_playlist()
    assert len(playlist_model.playlist) == 0, "Playlist should be empty after clearing"


# ##################################################
# # Tracklisting Management Test Cases
# ##################################################


def test_move_song_to_track_number(playlist_model, sample_playlist, mocker):
    """Test moving a song to a specific track number in the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    playlist_model.move_song_to_track_number(2, 1)  # Move Song 2 to the first position
    assert playlist_model.playlist[0] == 2, "Expected Song 2 to be in the first position"
    assert playlist_model.playlist[1] == 1, "Expected Song 1 to be in the second position"


def test_swap_songs_in_playlist(playlist_model, sample_playlist, mocker):
    """Test swapping the positions of two songs in the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    playlist_model.swap_songs_in_playlist(1, 2)  # Swap positions of Song 1 and Song 2
    assert playlist_model.playlist[0] == 2, "Expected Song 2 to be in the first position"
    assert playlist_model.playlist[1] == 1, "Expected Song 1 to be in the second position"


def test_swap_song_with_itself(playlist_model, song_beatles, mocker):
    """Test swapping the position of a song with itself raises an error."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=[song_beatles] * 2)
    playlist_model.playlist.append(1)

    with pytest.raises(ValueError, match="Cannot swap a song with itself"):
        playlist_model.swap_songs_in_playlist(1, 1)  # Swap positions of Song 1 with itself


def test_move_song_to_end(playlist_model, sample_playlist, mocker):
    """Test moving a song to the end of the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    playlist_model.move_song_to_end(1)  # Move Song 1 to the end
    assert playlist_model.playlist[1] == 1, "Expected Song 1 to be at the end"


def test_move_song_to_beginning(playlist_model, sample_playlist, mocker):
    """Test moving a song to the beginning of the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    playlist_model.move_song_to_beginning(2)  # Move Song 2 to the beginning
    assert playlist_model.playlist[0] == 2, "Expected Song 2 to be at the beginning"


##################################################
# Song Retrieval Test Cases
##################################################


def test_get_song_by_track_number(playlist_model, song_beatles, mocker):
    """Test successfully retrieving a song from the playlist by track number."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_beatles)
    playlist_model.playlist.append(1)

    retrieved_song = playlist_model.get_song_by_track_number(1)
    assert retrieved_song.id == 1
    assert retrieved_song.title == 'Come Together'
    assert retrieved_song.artist == 'The Beatles'
    assert retrieved_song.year == 1969
    assert retrieved_song.duration == 259
    assert retrieved_song.genre == 'Rock'


def test_get_all_songs(playlist_model, sample_playlist, mocker):
    """Test successfully retrieving all songs from the playlist."""
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    all_songs = playlist_model.get_all_songs()

    assert len(all_songs) == 2
    assert all_songs[0].id == 1
    assert all_songs[1].id == 2


def test_get_song_by_song_id(playlist_model, song_beatles, mocker):
    """Test successfully retrieving a song from the playlist by song ID."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_beatles)
    playlist_model.playlist.append(1)

    retrieved_song = playlist_model.get_song_by_song_id(1)

    assert retrieved_song.id == 1
    assert retrieved_song.title == 'Come Together'
    assert retrieved_song.artist == 'The Beatles'
    assert retrieved_song.year == 1969
    assert retrieved_song.duration == 259
    assert retrieved_song.genre == 'Rock'


def test_get_current_song(playlist_model, song_beatles, mocker):
    """Test successfully retrieving the current song from the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_beatles)

    playlist_model.playlist.append(1)

    current_song = playlist_model.get_current_song()
    assert current_song.id == 1
    assert current_song.title == 'Come Together'
    assert current_song.artist == 'The Beatles'
    assert current_song.year == 1969
    assert current_song.duration == 259
    assert current_song.genre == 'Rock'


def test_get_playlist_length(playlist_model):
    """Test getting the length of the playlist."""
    playlist_model.playlist.extend([1, 2])
    assert playlist_model.get_playlist_length() == 2, "Expected playlist length to be 2"


def test_get_playlist_duration(playlist_model, sample_playlist, mocker):
    """Test getting the total duration of the playlist."""
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", side_effect=sample_playlist)
    playlist_model.playlist.extend([1, 2])
    assert playlist_model.get_playlist_duration() == 560, "Expected playlist duration to be 560 seconds"


##################################################
# Utility Function Test Cases
##################################################


def test_check_if_empty_non_empty_playlist(playlist_model):
    """Test check_if_empty does not raise error if playlist is not empty."""
    playlist_model.playlist.append(1)
    try:
        playlist_model.check_if_empty()
    except ValueError:
        pytest.fail("check_if_empty raised ValueError unexpectedly on non-empty playlist")


def test_check_if_empty_empty_playlist(playlist_model):
    """Test check_if_empty raises error when playlist is empty."""
    playlist_model.clear_playlist()
    with pytest.raises(ValueError, match="Playlist is empty"):
        playlist_model.check_if_empty()


def test_validate_song_id(playlist_model, mocker):
    """Test validate_song_id does not raise error for valid song ID."""
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", return_value=True)

    playlist_model.playlist.append(1)
    try:
        playlist_model.validate_song_id(1)
    except ValueError:
        pytest.fail("validate_song_id raised ValueError unexpectedly for valid song ID")


def test_validate_song_id_no_check_in_playlist(playlist_model, mocker):
    """Test validate_song_id does not raise error for valid song ID when the id isn't in the playlist."""
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", return_value=True)
    try:
        playlist_model.validate_song_id(1, check_in_playlist=False)
    except ValueError:
        pytest.fail("validate_song_id raised ValueError unexpectedly for valid song ID")


def test_validate_song_id_invalid_id(playlist_model):
    """Test validate_song_id raises error for invalid song ID."""
    with pytest.raises(ValueError, match="Invalid song id: -1"):
        playlist_model.validate_song_id(-1)

    with pytest.raises(ValueError, match="Invalid song id: invalid"):
        playlist_model.validate_song_id("invalid")


def test_validate_song_id_not_in_playlist(playlist_model, song_nirvana, mocker):
    """Test validate_song_id raises error for song ID not in the playlist."""
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", return_value=song_nirvana)
    playlist_model.playlist.append(1)
    with pytest.raises(ValueError, match="Song with id 2 not found in playlist"):
        playlist_model.validate_song_id(2)


def test_validate_track_number(playlist_model):
    """Test validate_track_number does not raise error for valid track number."""
    playlist_model.playlist.append(1)
    try:
        playlist_model.validate_track_number(1)
    except ValueError:
        pytest.fail("validate_track_number raised ValueError unexpectedly for valid track number")

@pytest.mark.parametrize("track_number, expected_error", [
    (0, "Invalid track number: 0"),
    (2, "Invalid track number: 2"),
    ("invalid", "Invalid track number: invalid"),
])
def test_validate_track_number_invalid(playlist_model, track_number, expected_error):
    """Test validate_track_number raises error for invalid track numbers."""
    playlist_model.playlist.append(1)

    with pytest.raises(ValueError, match=expected_error):
        playlist_model.validate_track_number(track_number)



##################################################
# Playback Test Cases
##################################################


def test_play_current_song(playlist_model, sample_playlist, mocker):
    """Test playing the current song."""
    mock_update_play_count = mocker.patch("playlist.models.playlist_model.Songs.update_play_count")
    mocker.patch("playlist.models.playlist_model.Songs.get_song_by_id", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])

    playlist_model.play_current_song()

    # Assert that CURRENT_TRACK_NUMBER has been updated to 2
    assert playlist_model.current_track_number == 2, f"Expected track number to be 2, but got {playlist_model.current_track_number}"

    # Assert that update_play_count was called with the id of the first song
    mock_update_play_count.assert_called_once_with()

    # Get the second song from the iterator (which will increment CURRENT_TRACK_NUMBER back to 1)
    playlist_model.play_current_song()

    # Assert that CURRENT_TRACK_NUMBER has been updated back to 1
    assert playlist_model.current_track_number == 1, f"Expected track number to be 1, but got {playlist_model.current_track_number}"

    # Assert that update_play_count was called with the id of the second song
    mock_update_play_count.assert_called_with()


def test_rewind_playlist(playlist_model):
    """Test rewinding the iterator to the beginning of the playlist."""
    playlist_model.playlist.extend([1, 2])
    playlist_model.current_track_number = 2

    playlist_model.rewind_playlist()
    assert playlist_model.current_track_number == 1, "Expected to rewind to the first track"


def test_go_to_track_number(playlist_model):
    """Test moving the iterator to a specific track number in the playlist."""
    playlist_model.playlist.extend([1, 2])

    playlist_model.go_to_track_number(2)
    assert playlist_model.current_track_number == 2, "Expected to be at track 2 after moving song"


def test_go_to_random_track(playlist_model, mocker):
    """Test that go_to_random_track sets a valid random track number."""
    playlist_model.playlist.extend([1, 2])

    mocker.patch("playlist.models.playlist_model.get_random", return_value=2)

    playlist_model.go_to_random_track()
    assert playlist_model.current_track_number == 2, "Current track number should be set to the random value"


def test_play_entire_playlist(playlist_model, sample_playlist, mocker):
    """Test playing the entire playlist."""
    mock_update_play_count = mocker.patch("playlist.models.playlist_model.Songs.update_play_count")
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", side_effect=sample_playlist)

    playlist_model.playlist.extend([1,2])

    playlist_model.play_entire_playlist()

    # Check that all play counts were updated
    mock_update_play_count.assert_any_call()
    assert mock_update_play_count.call_count == len(playlist_model.playlist)

    # Check that the current track number was updated back to the first song
    assert playlist_model.current_track_number == 1, "Expected to loop back to the beginning of the playlist"


def test_play_rest_of_playlist(playlist_model, sample_playlist, mocker):
    """Test playing from the current position to the end of the playlist.

    """
    mock_update_play_count = mocker.patch("playlist.models.playlist_model.Songs.update_play_count")
    mocker.patch("playlist.models.playlist_model.PlaylistModel._get_song_from_cache_or_db", side_effect=sample_playlist)

    playlist_model.playlist.extend([1, 2])
    playlist_model.current_track_number = 2

    playlist_model.play_rest_of_playlist()

    # Check that play counts were updated for the remaining songs
    mock_update_play_count.assert_any_call()
    assert mock_update_play_count.call_count == 1

    assert playlist_model.current_track_number == 1, "Expected to loop back to the beginning of the playlist"