import logging
from typing import List

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ducks.db import db
from ducks.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


class Ducks(db.Model):
    """Represents a duck image in the system.

    This model maps to the 'ducks' table in the database and stores the urls of the duck image. 
    Used in a Flask-SQLAlchemy application to manage duck data for favorites.

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
    def get_duck_by_id(cls, duck_id: int) -> "Ducks":
        """Retrieve a duck by ID.

        Args:
            duck_id: The ID of the duck.

        Returns:
            Duck: The duck instance.

        Raises:
            ValueError: If the duck with the given ID does not exist.

        """
        logger.info(f"Attempting to retrieve duck with ID: {duck_id}")

        try:
            duck = db.session.get(cls, duck_id)
            if duck is None or not duck:
                logger.info(f"Duck with ID {duck_id} not found.")
                raise ValueError(f"Duck with ID {duck_id} not found.")

            logger.info(f"Successfully retrieved duck: {duck.id} - {duck.url}")
            return duck

        except SQLAlchemyError as e:
            logger.error(f"Database error while retrieving duck by ID {duck_id}: {e}")
            raise


    @classmethod
    def delete_duck(cls, duck_id: int) -> None:
        """Delete a duck by ID.

        Args:
            duck_id: The ID of the duck to delete.

        Raises:
            ValueError: If the duck with the given ID does not exist.

        """
        duck = cls.get_duck_by_id(duck_id)
        if duck is None:
            logger.info(f"Duck with ID {duck_id} not found.")
            raise ValueError(f"Duck with ID {duck_id} not found.")
        db.session.delete(duck)
        db.session.commit()
        logger.info(f"Duck with ID {duck_id} permanently deleted.")

