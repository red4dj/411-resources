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
            favorites (List[int]): The list of ids of the boxers in the ring.
            _ducks_cache (dict[int, Ducks]): A cache to store boxer objects for quick access.
            _ttl (dict[int, float]): A cache to store the time-to-live for each boxer.
            ttl_seconds (int): The time-to-live in seconds for the cached boxer objects.

        """
        self.favorites: List[int] = []
        self._ducks_cache: dict[int, Ducks] = {}
        self._ttl: dict[int, float] = {}
        self.ttl_seconds = int(os.getenv("TTL", 60))


    def clear_favorites(self):
        """Clears the list of favorite ducks.

        Clears all ducks from favorites. If the favorites list is empty, a warning is logged.

        """

        logger.info("Received reques to clear the favorites list.")

        if not self.favorites:
            logger.warning("Attempted to clear an empty ring.")
            return
        logger.info("Clearing the boxers from the ring.")
        self.favorites.clear()


    def enter_ring(self, boxer_id: int):
        """Prepares a boxer by adding them to the ring for an upcoming fight.

        Args:
            boxer_id (int): The ID of the boxer to enter the ring.

        Raises:
            ValueError: If the ring already has two boxers (fight is full).
            ValueError: If the boxer ID is invalid or the boxer does not exist.

        """
        if len(self.ring) >= 2:
            logger.error(f"Attempted to add boxer ID {boxer_id} but the ring is full")
            raise ValueError("Ring is full")

        try:
            boxer = Boxers.get_boxer_by_id(boxer_id)
        except ValueError as e:
            logger.error(str(e))
            raise

        logger.info(f"Adding boxer '{boxer.name}' (ID {boxer_id}) to the ring")
        self.ring.append(boxer_id)

        logger.info(f"Current boxers in the ring: {[Boxers.get_boxer_by_id(b).name for b in self.ring]}")


    def get_ducks(self) -> List[Ducks]:
        """Retrieves the current list of ducks in the favorites.

        Returns:
            List[Ducks]: A list of Boxers dataclass instances representing the boxers in the ring.

        """
        now = time.time()

        if not self.favorites:
            logger.warning("Retrieving ducks from an empty favorites.")
        else:
            logger.info(f"Retrieving {len(self.favorites)} ducks from favorites.")

        for duck_id in self.favorites:
            expired = not (self._ttl.get(duck_id, 0) > now)
            if expired:
                try:
                    duck = Ducks.get_duck_by_id(duck_id)
                    logger.info(f"Duck ID {duck_id} loaded from DB")
                except ValueError as e:
                    logger.error(f"Duck ID {duck_id} not found in DB: {e}")
                    raise ValueError(f"Duck ID {duck_id} not found in database") from e
                
                self._ducks_cache[duck_id] = duck
                self._ttl[duck_id] = now + self.ttl_seconds

            else:
                logger.debug(f"Using cached duck {duck_id} (TTL valid).")

        ducks = [self._ducks_cache[duck_id] for duck_id in self.favorites]
        logger.info(f"Retrieved {len(ducks)} ducks from favorites.")
        return ducks

    