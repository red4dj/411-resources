import logging
import os
import time
from typing import List

from playlist.models.song_model import Songs
from playlist.utils.api_utils import get_random
from playlist.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class PlaylistModel:
    """
    A class to manage a playlist of songs.

    """

    def __init__(self):
        """Initializes the PlaylistModel with an empty playlist and the current track set to 1.

        The playlist is a list of Songs, and the current track number is 1-indexed.
        The TTL (Time To Live) for song caching is set to a default value from the environment variable "TTL",
        which defaults to 60 seconds if not set.

        """
        self.current_track_number = 1
        self.playlist: List[int] = []
        self._song_cache: dict[int, Songs] = {}
        self._ttl: dict[int, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))  # Default TTL is 60 seconds


    ##################################################
    # Song Management Functions
    ##################################################

    def _get_song_from_cache_or_db(self, song_id: int) -> Songs:
        """
        Retrieves a song by ID, using the internal cache if possible.

        This method checks whether a cached version of the song is available
        and still valid. If not, it queries the database, updates the cache, and returns the song.

        Args:
            song_id (int): The unique ID of the song to retrieve.

        Returns:
            Songs: The song object corresponding to the given ID.

        Raises:
            ValueError: If the song cannot be found in the database.
        """
        now = time.time()

        if song_id in self._song_cache and self._ttl.get(song_id, 0) > now:
            logger.debug(f"Song ID {song_id} retrieved from cache")
            return self._song_cache[song_id]

        try:
            song = Songs.get_song_by_id(song_id)
            logger.info(f"Song ID {song_id} loaded from DB")
        except ValueError as e:
            logger.error(f"Song ID {song_id} not found in DB: {e}")
            raise ValueError(f"Song ID {song_id} not found in database") from e

        self._song_cache[song_id] = song
        self._ttl[song_id] = now + self.ttl_seconds
        return song

    def add_song_to_playlist(self, song_id: int) -> None:
        """
        Adds a song to the playlist by ID, using the cache or database lookup.

        Args:
            song_id (int): The ID of the song to add to the playlist.

        Raises:
            ValueError: If the song ID is invalid or already exists in the playlist.
        """
        logger.info(f"Received request to add song with ID {song_id} to the playlist")

        song_id = self.validate_song_id(song_id, check_in_playlist=False)

        if song_id in self.playlist:
            logger.error(f"Song with ID {song_id} already exists in the playlist")
            raise ValueError(f"Song with ID {song_id} already exists in the playlist")

        try:
            song = self._get_song_from_cache_or_db(song_id)
        except ValueError as e:
            logger.error(f"Failed to add song: {e}")
            raise

        self.playlist.append(song.id)
        logger.info(f"Successfully added to playlist: {song.artist} - {song.title} ({song.year})")


    def remove_song_by_song_id(self, song_id: int) -> None:
        """Removes a song from the playlist by its song ID.

        Args:
            song_id (int): The ID of the song to remove from the playlist.

        Raises:
            ValueError: If the playlist is empty or the song ID is invalid.

        """
        logger.info(f"Received request to remove song with ID {song_id}")

        self.check_if_empty()
        song_id = self.validate_song_id(song_id)

        if song_id not in self.playlist:
            logger.warning(f"Song with ID {song_id} not found in the playlist")
            raise ValueError(f"Song with ID {song_id} not found in the playlist")

        self.playlist.remove(song_id)
        logger.info(f"Successfully removed song with ID {song_id} from the playlist")

    def remove_song_by_track_number(self, track_number: int) -> None:
        """Removes a song from the playlist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the song to remove.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.

        """
        logger.info(f"Received request to remove song at track number {track_number}")

        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        playlist_index = track_number - 1

        logger.info(f"Successfully removed song at track number {track_number}")
        del self.playlist[playlist_index]

    def clear_playlist(self) -> None:
        """Clears all songs from the playlist.

        Clears all songs from the playlist. If the playlist is already empty, logs a warning.

        """
        logger.info("Received request to clear the playlist")

        try:
            if self.check_if_empty():
                pass
        except ValueError:
            logger.warning("Clearing an empty playlist")

        self.playlist.clear()
        logger.info("Successfully cleared the playlist")


    ##################################################
    # Playlist Retrieval Functions
    ##################################################


    def get_all_songs(self) -> List[Songs]:
        """Returns a list of all songs in the playlist using cached song data.

        Returns:
            List[Song]: A list of all songs in the playlist.

        Raises:
            ValueError: If the playlist is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving all songs in the playlist")
        return [self._get_song_from_cache_or_db(song_id) for song_id in self.playlist]

    def get_song_by_song_id(self, song_id: int) -> Songs:
        """Retrieves a song from the playlist by its song ID using the cache or DB.

        Args:
            song_id (int): The ID of the song to retrieve.

        Returns:
            Song: The song with the specified ID.

        Raises:
            ValueError: If the playlist is empty or the song is not found.
        """
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)
        logger.info(f"Retrieving song with ID {song_id} from the playlist")
        song = self._get_song_from_cache_or_db(song_id)
        logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
        return song

    def get_song_by_track_number(self, track_number: int) -> Songs:
        """Retrieves a song from the playlist by its track number (1-indexed).

        Args:
            track_number (int): The track number of the song to retrieve.

        Returns:
            Song: The song at the specified track number.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.
        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        playlist_index = track_number - 1

        logger.info(f"Retrieving song at track number {track_number} from playlist")
        song_id = self.playlist[playlist_index]
        song = self._get_song_from_cache_or_db(song_id)
        logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
        return song

    def get_current_song(self) -> Songs:
        """Returns the current song being played.

        Returns:
            Song: The currently playing song.

        Raises:
            ValueError: If the playlist is empty.
        """
        self.check_if_empty()
        logger.info("Retrieving the current song being played")
        return self.get_song_by_track_number(self.current_track_number)

    def get_playlist_length(self) -> int:
        """Returns the number of songs in the playlist.

        Returns:
            int: The total number of songs in the playlist.

        """
        length = len(self.playlist)
        logger.info(f"Retrieving playlist length: {length} songs")
        return length

    def get_playlist_duration(self) -> int:
        """
        Returns the total duration of the playlist in seconds using cached songs.

        Returns:
            int: The total duration of all songs in the playlist in seconds.
        """
        total_duration = sum(self._get_song_from_cache_or_db(song_id).duration for song_id in self.playlist)
        logger.info(f"Retrieving total playlist duration: {total_duration} seconds")
        return total_duration


    ##################################################
    # Playlist Movement Functions
    ##################################################


    def go_to_track_number(self, track_number: int) -> None:
        """Sets the current track number to the specified track number.

        Args:
            track_number (int): The track number to set as the current track.

        Raises:
            ValueError: If the playlist is empty or the track number is invalid.

        """
        self.check_if_empty()
        track_number = self.validate_track_number(track_number)
        logger.info(f"Setting current track number to {track_number}")
        self.current_track_number = track_number

    def go_to_random_track(self) -> None:
        """Sets the current track number to a randomly selected track.

        Raises:
            ValueError: If the playlist is empty.

        """
        self.check_if_empty()

        # Get a random index using the random.org API
        random_track = get_random(self.get_playlist_length())

        logger.info(f"Setting current track number to random track: {random_track}")
        self.current_track_number = random_track

    def move_song_to_beginning(self, song_id: int) -> None:
        """Moves a song to the beginning of the playlist.

        Args:
            song_id (int): The ID of the song to move.

        Raises:
            ValueError: If the playlist is empty or the song ID is invalid.

        """
        logger.info(f"Moving song with ID {song_id} to the beginning of the playlist")
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)

        self.playlist.remove(song_id)
        self.playlist.insert(0, song_id)

        logger.info(f"Successfully moved song with ID {song_id} to the beginning")

    def move_song_to_end(self, song_id: int) -> None:
        """Moves a song to the end of the playlist.

        Args:
            song_id (int): The ID of the song to move.

        Raises:
            ValueError: If the playlist is empty or the song ID is invalid.

        """
        logger.info(f"Moving song with ID {song_id} to the end of the playlist")
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)

        self.playlist.remove(song_id)
        self.playlist.append(song_id)

        logger.info(f"Successfully moved song with ID {song_id} to the end")

    def move_song_to_track_number(self, song_id: int, track_number: int) -> None:
        """Moves a song to a specific track number in the playlist.

        Args:
            song_id (int): The ID of the song to move.
            track_number (int): The track number to move the song to (1-indexed).

        Raises:
            ValueError: If the playlist is empty, the song ID is invalid, or the track number is out of range.

        """
        logger.info(f"Moving song with ID {song_id} to track number {track_number}")
        self.check_if_empty()
        song_id = self.validate_song_id(song_id)
        track_number = self.validate_track_number(track_number)

        playlist_index = track_number - 1

        self.playlist.remove(song_id)
        self.playlist.insert(playlist_index, song_id)

        logger.info(f"Successfully moved song with ID {song_id} to track number {track_number}")

    def swap_songs_in_playlist(self, song1_id: int, song2_id: int) -> None:
        """Swaps the positions of two songs in the playlist.

        Args:
            song1_id (int): The ID of the first song to swap.
            song2_id (int): The ID of the second song to swap.

        Raises:
            ValueError: If the playlist is empty, either song ID is invalid, or attempting to swap the same song.

        """
        logger.info(f"Swapping songs with IDs {song1_id} and {song2_id}")
        self.check_if_empty()
        song1_id = self.validate_song_id(song1_id)
        song2_id = self.validate_song_id(song2_id)

        if song1_id == song2_id:
            logger.error(f"Cannot swap a song with itself: {song1_id}")
            raise ValueError(f"Cannot swap a song with itself: {song1_id}")

        index1, index2 = self.playlist.index(song1_id), self.playlist.index(song2_id)

        self.playlist[index1], self.playlist[index2] = self.playlist[index2], self.playlist[index1]

        logger.info(f"Successfully swapped songs with IDs {song1_id} and {song2_id}")


    ##################################################
    # Playlist Playback Functions
    ##################################################


    def play_current_song(self) -> None:
        """Plays the current song and advances the playlist.

        Raises:
            ValueError: If the playlist is empty.

        """
        self.check_if_empty()
        current_song = self.get_song_by_track_number(self.current_track_number)

        logger.info(f"Playing song: {current_song.title} (ID: {current_song.id}) at track number: {self.current_track_number}")
        current_song.update_play_count()
        logger.info(f"Updated play count for song: {current_song.title} (ID: {current_song.id})")

        self.current_track_number = (self.current_track_number % self.get_playlist_length()) + 1
        logger.info(f"Advanced to track number: {self.current_track_number}")

    def play_entire_playlist(self) -> None:
        """Plays all songs in the playlist from the beginning.

        Raises:
            ValueError: If the playlist is empty.

        """
        self.check_if_empty()
        logger.info("Starting to play the entire playlist.")

        self.current_track_number = 1
        for _ in range(self.get_playlist_length()):
            self.play_current_song()

        logger.info("Finished playing the entire playlist.")

    def play_rest_of_playlist(self) -> None:
        """Plays the remaining songs in the playlist from the current track onward.

        Raises:
            ValueError: If the playlist is empty.

        """
        self.check_if_empty()
        logger.info(f"Playing the rest of the playlist from track number: {self.current_track_number}")

        for _ in range(self.get_playlist_length() - self.current_track_number + 1):
            self.play_current_song()

        logger.info("Finished playing the rest of the playlist.")

    def rewind_playlist(self) -> None:
        """Resets the playlist to the first track.

        Raises:
            ValueError: If the playlist is empty.

        """
        self.check_if_empty()
        self.current_track_number = 1
        logger.info("Rewound playlist to the first track.")


    ##################################################
    # Utility Functions
    ##################################################


    ####################################################################################################
    #
    # Note: I am only testing these things once. EG I am not testing that everything rejects an empty
    # list as they all do so by calling this helper
    #
    ####################################################################################################

    def validate_song_id(self, song_id: int, check_in_playlist: bool = True) -> int:
        """
        Validates the given song ID.

        Args:
            song_id (int): The song ID to validate.
            check_in_playlist (bool, optional): If True, verifies the ID is present in the playlist.
                                                If False, skips that check. Defaults to True.

        Returns:
            int: The validated song ID.

        Raises:
            ValueError: If the song ID is not a non-negative integer,
                        not found in the playlist (if check_in_playlist=True),
                        or not found in the database.
        """
        try:
            song_id = int(song_id)
            if song_id < 0:
                raise ValueError
        except ValueError:
            logger.error(f"Invalid song id: {song_id}")
            raise ValueError(f"Invalid song id: {song_id}")

        if check_in_playlist and song_id not in self.playlist:
            logger.error(f"Song with id {song_id} not found in playlist")
            raise ValueError(f"Song with id {song_id} not found in playlist")

        try:
            self._get_song_from_cache_or_db(song_id)
        except Exception as e:
            logger.error(f"Song with id {song_id} not found in database: {e}")
            raise ValueError(f"Song with id {song_id} not found in database")

        return song_id

    def validate_track_number(self, track_number: int) -> int:
        """
        Validates the given track number, ensuring it is within the playlist's range.

        Args:
            track_number (int): The track number to validate.

        Returns:
            int: The validated track number.

        Raises:
            ValueError: If the track number is not a valid positive integer or is out of range.

        """
        try:
            track_number = int(track_number)
            if not (1 <= track_number <= self.get_playlist_length()):
                raise ValueError(f"Invalid track number: {track_number}")
        except ValueError as e:
            logger.error(f"Invalid track number: {track_number}")
            raise ValueError(f"Invalid track number: {track_number}") from e

        return track_number

    def check_if_empty(self) -> None:
        """
        Checks if the playlist is empty and raises a ValueError if it is.

        Raises:
            ValueError: If the playlist is empty.

        """
        if not self.playlist:
            logger.error("Playlist is empty")
            raise ValueError("Playlist is empty")
