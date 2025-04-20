import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from playlist.db import db
from playlist.utils.logger import configure_logger
from playlist.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class Songs(db.Model):
    """Represents a song in the catalog.

    This model maps to the 'songs' table and stores metadata such as artist,
    title, genre, release year, and duration. It also tracks play count.

    Used in a Flask-SQLAlchemy application for playlist management,
    user interaction, and data-driven song operations.
    """

    __tablename__ = "Songs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artist = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    genre = db.Column(db.String, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    play_count = db.Column(db.Integer, nullable=False, default=0)

    def validate(self) -> None:
        """Validates the song instance before committing to the database.

        Raises:
            ValueError: If any required fields are invalid.
        """
        if not self.artist or not isinstance(self.artist, str):
            raise ValueError("Artist must be a non-empty string.")
        if not self.title or not isinstance(self.title, str):
            raise ValueError("Title must be a non-empty string.")
        if not isinstance(self.year, int) or self.year <= 1900:
            raise ValueError("Year must be an integer greater than 1900.")
        if not self.genre or not isinstance(self.genre, str):
            raise ValueError("Genre must be a non-empty string.")
        if not isinstance(self.duration, int) or self.duration <= 0:
            raise ValueError("Duration must be a positive integer.")

    @classmethod
    def create_song(cls, artist: str, title: str, year: int, genre: str, duration: int) -> None:
        """
        Creates a new song in the songs table using SQLAlchemy.

        Args:
            artist (str): The artist's name.
            title (str): The song title.
            year (int): The year the song was released.
            genre (str): The song genre.
            duration (int): The duration of the song in seconds.

        Raises:
            ValueError: If any field is invalid or if a song with the same compound key already exists.
            SQLAlchemyError: For any other database-related issues.
        """
        logger.info(f"Received request to create song: {artist} - {title} ({year})")

        try:
            song = Songs(
                artist=artist.strip(),
                title=title.strip(),
                year=year,
                genre=genre.strip(),
                duration=duration
            )
            song.validate()
        except ValueError as e:
            logger.warning(f"Validation failed: {e}")
            raise

        try:
            # Check for existing song with same compound key (artist, title, year)
            existing = Songs.query.filter_by(artist=artist.strip(), title=title.strip(), year=year).first()
            if existing:
                logger.error(f"Song already exists: {artist} - {title} ({year})")
                raise ValueError(f"Song with artist '{artist}', title '{title}', and year {year} already exists.")

            db.session.add(song)
            db.session.commit()
            logger.info(f"Song successfully added: {artist} - {title} ({year})")

        except IntegrityError:
            logger.error(f"Song already exists: {artist} - {title} ({year})")
            db.session.rollback()
            raise ValueError(f"Song with artist '{artist}', title '{title}', and year {year} already exists.")

        except SQLAlchemyError as e:
            logger.error(f"Database error while creating song: {e}")
            db.session.rollback()
            raise

    @classmethod
    def delete_song(cls, song_id: int) -> None:
        """
        Permanently deletes a song from the catalog by ID.

        Args:
            song_id (int): The ID of the song to delete.

        Raises:
            ValueError: If the song with the given ID does not exist.
            SQLAlchemyError: For any database-related issues.
        """
        logger.info(f"Received request to delete song with ID {song_id}")

        try:
            song = cls.query.get(song_id)
            if not song:
                logger.warning(f"Attempted to delete non-existent song with ID {song_id}")
                raise ValueError(f"Song with ID {song_id} not found")

            db.session.delete(song)
            db.session.commit()
            logger.info(f"Successfully deleted song with ID {song_id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting song with ID {song_id}: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_song_by_id(cls, song_id: int) -> "Songs":
        """
        Retrieves a song from the catalog by its ID.

        Args:
            song_id (int): The ID of the song to retrieve.

        Returns:
            Songs: The song instance corresponding to the ID.

        Raises:
            ValueError: If no song with the given ID is found.
            SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve song with ID {song_id}")

        try:
            song = cls.query.get(song_id)

            if not song:
                logger.info(f"Song with ID {song_id} not found")
                raise ValueError(f"Song with ID {song_id} not found")

            logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
            return song

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving song by ID {song_id}: {e}")
            raise

    @classmethod
    def get_song_by_compound_key(cls, artist: str, title: str, year: int) -> "Songs":
        """
        Retrieves a song from the catalog by its compound key (artist, title, year).

        Args:
            artist (str): The artist of the song.
            title (str): The title of the song.
            year (int): The year the song was released.

        Returns:
            Songs: The song instance matching the provided compound key.

        Raises:
            ValueError: If no matching song is found.
            SQLAlchemyError: If a database error occurs.
        """
        logger.info(f"Attempting to retrieve song with artist '{artist}', title '{title}', and year {year}")

        try:
            song = cls.query.filter_by(artist=artist.strip(), title=title.strip(), year=year).first()

            if not song:
                logger.info(f"Song with artist '{artist}', title '{title}', and year {year} not found")
                raise ValueError(f"Song with artist '{artist}', title '{title}', and year {year} not found")

            logger.info(f"Successfully retrieved song: {song.artist} - {song.title} ({song.year})")
            return song

        except SQLAlchemyError as e:
            logger.error(
                f"Database error while retrieving song by compound key "
                f"(artist '{artist}', title '{title}', year {year}): {e}"
            )
            raise

    @classmethod
    def get_all_songs(cls, sort_by_play_count: bool = False) -> list[dict]:
        """
        Retrieves all songs from the catalog as dictionaries.

        Args:
            sort_by_play_count (bool): If True, sort the songs by play count in descending order.

        Returns:
            list[dict]: A list of dictionaries representing all songs with play_count.

        Raises:
            SQLAlchemyError: If any database error occurs.
        """
        logger.info("Attempting to retrieve all songs from the catalog")

        try:
            query = cls.query
            if sort_by_play_count:
                query = query.order_by(cls.play_count.desc())

            songs = query.all()

            if not songs:
                logger.warning("The song catalog is empty.")
                return []

            results = [
                {
                    "id": song.id,
                    "artist": song.artist,
                    "title": song.title,
                    "year": song.year,
                    "genre": song.genre,
                    "duration": song.duration,
                    "play_count": song.play_count,
                }
                for song in songs
            ]

            logger.info(f"Retrieved {len(results)} songs from the catalog")
            return results

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving all songs: {e}")
            raise

    @classmethod
    def get_random_song(cls) -> dict:
        """
        Retrieves a random song from the catalog as a dictionary.

        Returns:
            dict: A randomly selected song dictionary.
        """
        all_songs = cls.get_all_songs()

        if not all_songs:
            logger.warning("Cannot retrieve random song because the song catalog is empty.")
            raise ValueError("The song catalog is empty.")

        index = get_random(len(all_songs))
        logger.info(f"Random index selected: {index} (total songs: {len(all_songs)})")

        return all_songs[index - 1]

    def update_play_count(self) -> None:
        """
        Increments the play count of the current song instance.

        Raises:
            ValueError: If the song does not exist in the database.
            SQLAlchemyError: If any database error occurs.
        """

        logger.info(f"Attempting to update play count for song with ID {self.id}")

        try:
            song = Songs.query.get(self.id)
            if not song:
                logger.warning(f"Cannot update play count: Song with ID {self.id} not found.")
                raise ValueError(f"Song with ID {self.id} not found")

            song.play_count += 1
            db.session.commit()

            logger.info(f"Play count incremented for song with ID: {self.id}")

        except SQLAlchemyError as e:
            logger.error(f"Database error while updating play count for song with ID {self.id}: {e}")
            db.session.rollback()
            raise
