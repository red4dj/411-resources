import logging
import math
import os
import time
from typing import List

from ducks.models.ducks_model import Ducks
from ducks.utils.logger import configure_logger
from ducks.utils.api_utils import get_random


logger = logging.getLogger(__name__)
configure_logger(logger)


class FavoritesModel:
    """A class to manage the the saved favorite ducks of a user.

    """

    def __init__(self):
        """Initializes the Favorites with an empty list of ducks.

        The favorites are initially empty, and the ducks cache and time-to-live (TTL) caches are also initialized.
        The TTL is set to 60 seconds by default, but this can be overridden by setting the TTL_SECONDS environment variable.

        Attributes:
            favorites (List[int]): The list of ids of the ducks in favorites.
            _ducks_cache (dict[int, Ducks]): A cache to store duck objects for quick access.
            _ttl (dict[int, float]): A cache to store the time-to-live for each duck.
            ttl_seconds (int): The time-to-live in seconds for the cached duck objects.

        """
        self.favorites: List[int] = []
        self._ducks_cache: dict[int, Ducks] = {}
        self._ttl: dict[int, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))


    def _get_duck_from_cache_or_db(self, duck_id: int) -> Ducks:
        """
        Retrieves a duck by ID, using the internal cache if possible.

        This method checks whether a cached version of the duck is available
        and still valid. If not, it queries the database, updates the cache, and returns the duck.

        Args:
            duck_id (int): The unique ID of the duck to retrieve.

        Returns:
            Ducks: The duck object corresponding to the given ID.

        Raises:
            ValueError: If the duck cannot be found in the database.
        """
        now = time.time()

        if duck_id in self._ducks_cache and self._ttl.get(duck_id, 0) > now:
            logger.debug(f"Duck ID {duck_id} retrieved from cache")
            return self._ducks_cache[duck_id]

        try:
            duck = Ducks.get_duck_by_id(duck_id)
            logger.info(f"Duck ID {duck_id} loaded from DB")
        except ValueError as e:
            logger.error(f"Duck ID {duck_id} not found in DB: {e}")
            raise ValueError(f"Duck ID {duck_id} not found in database") from e

        self._ducks_cache[duck_id] = duck
        self._ttl[duck_id] = now + self.ttl_seconds
        return duck


    def clear_favorites(self):
        """Clears the list of favorite ducks.

        Clears all ducks from favorites. If the favorites list is empty, a warning is logged.

        """

        logger.info("Received reques to clear the favorites list.")

        if not self.favorites:
            logger.warning("Attempted to clear an empty favorites list.")
            return
        logger.info("Clearing the ducks from favorites.")
        self.favorites.clear()

    def remove_duck_by_duck_id(self, duck_id: int) -> None:
        """Removes a duck from favorites by its ID.

        Args:
            duck_id (int): The ID of the duck to remove from favorites.

        Raises:
            ValueError: If favorites is empty or the duck ID is invalid.

        """
        logger.info(f"Received request to remove duck with ID {duck_id}")

        if not self.favorites:
            logger.warning("Attempted to remove a duck from an empty favorites list.")
            raise ValueError("Favorites list is empty.")
        
        if not duck_id or not isinstance(duck_id, int):
            logger.error(f"Invalid duck ID: {duck_id}")
            raise ValueError("Invalid duck ID.")
        

        if duck_id not in self.favorites:
            logger.warning(f"Duck with ID {duck_id} not found in favorites")
            raise ValueError(f"Duck with ID {duck_id} not found in favorites")

        self.favorites.remove(duck_id)
        logger.info(f"Successfully removed duck with ID {duck_id} from favorites.")


    def add_duck_to_favorites(self, duck_id: int):
        """
        Adds a duck to favorites by ID, using the cache or database lookup.

        Args:
            duck_id (int): The ID of the duck to add to the favorites.

        Raises:
            ValueError: If the duck ID is invalid or already exists in favorites.
        """

        if duck_id in self.favorites:
            logger.error(f"Duck with ID {duck_id} already exists in favorites")
            raise ValueError(f"Duck with ID {duck_id} already exists in favorites")


        try:
            duck = self._get_duck_from_cache_or_db(duck_id)
        except ValueError as e:
            logger.error(str(e))
            raise

        logger.info(f"Adding duck '{duck.url}' (ID {duck_id}) to favorites.")
        self.favorites.append(duck_id)


    def get_duck_by_duck_id(self, duck_id: int) -> Ducks:
        """Retrieves a duck from favorites by its duck ID using the cache or DB.

        Args:
            duck_id (int): The ID of the duck to retrieve.

        Returns:
            Duck: The duck with the specified ID.

        Raises:
            ValueError: If favorites is empty or the duck is not found.
        """
        if not self.favorites:
            logger.warning("Attempted to retrieve a duck from an empty favorites list.")
            raise ValueError("Favorites list is empty.")
        
        if not duck_id or not isinstance(duck_id, int):
            logger.error(f"Invalid duck ID: {duck_id}")
            raise ValueError("Invalid duck ID.")
        
        logger.info(f"Retrieving duck with ID {duck_id} from favorites")
        duck = self._get_duck_from_cache_or_db(duck_id)
        logger.info(f"Successfully retrieved duck: {duck.url}")
        return duck


    def get_ducks(self) -> List[Ducks]:
        """Returns a list of all ducks in favorites using cached duck data.

        Returns:
            List[Duck]: A list of all duck in favorites.

        Raises:
            ValueError: If the favorites is empty.
        """
        if not self.favorites:
            logger.warning("Attempted to retrieve ducks from an empty favorites list.")
            raise ValueError("Favorites list is empty.")
        
        logger.info("Retrieving all ducks in favorites")
        return [self._get_duck_from_cache_or_db(duck_id) for duck_id in self.favorites]

    