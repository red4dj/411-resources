import logging
import os
import requests

from playlist.utils.logger import configure_logger


RANDOM_ORG_BASE_URL = os.getenv("RANDOM_ORG_BASE_URL",
                                "https://www.random.org/integers/?num=1&min=1&col=1&base=10&format=plain&rnd=new")


logger = logging.getLogger(__name__)
configure_logger(logger)


def get_random(max: int) -> int:
    """
    Fetches a random integer between 1 and max inclusive from random.org.

    Args:
        max (int): The upper bound (inclusive) for the random number.

    Returns:
        int: A random number between 1 and max.

    Raises:
        RuntimeError: If the request to random.org fails.
        ValueError: If the response from random.org is not a valid integer.
    """
    if max < 1:
        raise ValueError("max must be at least 1")

    # Construct the full URL dynamically
    url = f"{RANDOM_ORG_BASE_URL}&max={max}"

    try:
        # Log the request to random.org
        logger.info(f"Fetching random number from {url}")

        response = requests.get(url, timeout=5)
        response.raise_for_status()

        random_number_str = response.text.strip()

        try:
            random_number = int(random_number_str)
        except ValueError:
            logger.error(f"Invalid response from random.org: {random_number_str}")
            raise ValueError(f"Invalid response from random.org: {random_number_str}")

        logger.info(f"Received random number: {random_number}")
        return random_number

    except requests.exceptions.Timeout:
        logger.error("Request to random.org timed out.")
        raise RuntimeError("Request to random.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to random.org failed: {e}")
        raise RuntimeError(f"Request to random.org failed: {e}")
