import logging
from typing import List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ducks.db import db
from ducks.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


class Ducks(db.Model):
    """Represents a competitive boxer in the system.

    This model maps to the 'boxers' table in the database and stores personal
    and performance-related attributes such as name, weight, height, reach,
    age, and fight statistics. Used in a Flask-SQLAlchemy application to
    manage boxer data, run simulations, and track fight outcomes.

    """
    __tablename__ = "Boxers"

    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    url = db.Column(db.String, nullable=False)


    def __init__(self, url: str):
        """Initialize a new Duck instance with basic attributes.

        Args:
            url: The URL of the duck image.

        """
        self.id = None
        self.url = url

    def validate(self) -> None:
        """Validates the duck instance before committing to the database.

        Raises:
            ValueError: If any required fields are invalid.
        """
        if not self.url or not isinstance(self.url, str):
            raise ValueError("URL must be a non-empty string.")


    @classmethod
    def create_duck(cls, url: str) -> None:
        """Create and persist a new Duck instance.

        Args:
            url: The URL of the duck image.

        Raises:
            IntegrityError: If a boxer with the same URL already exists.
            ValueError: If the input parameters are invalid.
            SQLAlchemyError: If there is a database error during creation.

        """
        logger.info(f"Creating Duck: {url}")

        try:
            duck = Ducks(
                url = url.strip()
            )
            duck.validate()

        except ValueError as e:
            logger.warning(f"Validation failed: {e}")
            raise

        # Check for existing boxer with same name
        existing = Ducks.query.filter_by(url=url.strip()).first()
        if existing:
            logger.error(f"Duck already exists: {url.strip()}")
            raise ValueError(f"Duck already exists: {url.strip()}")

        try:
            db.session.add(duck)
            db.session.commit()
            logger.info(f"Duck created successfully: {url}")
        except IntegrityError:
            logger.error(f"Duck at '{url}' already exists.")
            db.session.rollback()
            raise IntegrityError(f"Duck at '{url}' already exists.")
        except SQLAlchemyError as e:
            logger.error(f"Database error during creation: {e}")
            db.session.rollback()
            raise

    @classmethod
    def get_boxer_by_id(cls, boxer_id: int) -> "Boxers":
        """Retrieve a boxer by ID.

        Args:
            boxer_id: The ID of the boxer.

        Returns:
            Boxer: The boxer instance.

        Raises:
            ValueError: If the boxer with the given ID does not exist.

        """
        logger.info(f"Attempting to retrieve boxer with ID: {boxer_id}")

        try:
            boxer = db.session.get(cls, boxer_id)
            if boxer is None or not boxer:
                logger.info(f"Boxer with ID {boxer_id} not found.")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            logger.info(f"Successfully retrieved boxer: {boxer.id} - {boxer.name}")
            return boxer

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving boxer by ID {boxer_id}: {e}")
            raise

    @classmethod
    def get_boxer_by_name(cls, name: str) -> "Boxers":
        """Retrieve a boxer by name.

        Args:
            name: The name of the boxer.

        Returns:
            Boxer: The boxer instance.

        Raises:
            ValueError: If the boxer with the given name does not exist.

        """
        logger.info(f"Attempting to retrieve boxer: {name}")

        try:
            boxer = cls.query.filter_by(name=name.strip()).first()

            if not boxer or boxer is None:
                logger.info(f"Boxer '{name.strip()}' not found.")
                raise ValueError(f"Boxer '{name.strip()}' not found.")

            logger.info(f"Successfully retrieved boxer: {boxer.name}")
            return boxer

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving boxer: '{name}': {e}")
            raise

    @classmethod
    def delete(cls, boxer_id: int) -> None:
        """Delete a boxer by ID.

        Args:
            boxer_id: The ID of the boxer to delete.

        Raises:
            ValueError: If the boxer with the given ID does not exist.

        """
        boxer = cls.get_boxer_by_id(boxer_id)
        if boxer is None:
            logger.info(f"Boxer with ID {boxer_id} not found.")
            raise ValueError(f"Boxer with ID {boxer_id} not found.")
        db.session.delete(boxer)
        db.session.commit()
        logger.info(f"Boxer with ID {boxer_id} permanently deleted.")

    def update_stats(self, result: str) -> None:
        """Update the boxer's fight and win count based on result.

        Args:
            result: The result of the fight ('win' or 'loss').

        Raises:
            ValueError: If the result is not 'win' or 'loss'.
            ValueError: If the number of wins exceeds the number of fights.

        """
        if result not in {"win", "loss"}:
            raise ValueError("Result must be 'win' or 'loss'.")

        self.fights += 1
        if result == "win":
            self.wins += 1

        if self.wins > self.fights:
            raise ValueError("Wins cannot exceed number of fights.")

        db.session.commit()
        logger.info(f"Updated stats for boxer {self.name}: {self.fights} fights, {self.wins} wins.")

    @staticmethod
    def get_leaderboard(sort_by: str = "wins") -> List[dict]:
        """Retrieve a sorted leaderboard of boxers.

        Args:
            sort_by (str): Either "wins" or "win_pct".

        Returns:
            List[Dict]: List of boxers with stats and win percentage.

        Raises:
            ValueError: If the sort_by parameter is not valid.

        """
        logger.info(f"Retrieving leaderboard. Sort by: {sort_by}")

        if sort_by not in {"wins", "win_pct"}:
            logger.error(f"Invalid sort_by parameter: {sort_by}")
            raise ValueError(f"Invalid sort_by parameter: {sort_by}")

        boxers = Boxers.query.filter(Boxers.fights > 0).all()

        def compute_win_pct(b: Boxers) -> float:
            return round((b.wins / b.fights) * 100, 1) if b.fights > 0 else 0.0

        leaderboard = [{
            "id": b.id,
            "name": b.name,
            "weight": b.weight,
            "height": b.height,
            "reach": b.reach,
            "age": b.age,
            "weight_class": b.weight_class,
            "fights": b.fights,
            "wins": b.wins,
            "win_pct": compute_win_pct(b)
        } for b in boxers]

        leaderboard.sort(key=lambda b: b[sort_by], reverse=True)
        logger.info("Leaderboard retrieved successfully.")
        return leaderboard
