import logging
import os
import requests
from random import choice
from json import loads
from ducks.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


RANDOM_DUCK_URL = os.getenv("RANDOM_DUCK_URL", "https://random-d.uk/api/v2/quack")
SOUND_QUACK_URL = os.getenv("SOUND_QUACK_URL", "https://freesound.org/apiv2/search/text/?query=duck%20quack&format=json")
SOUND_TOKEN = os.getenv("SOUND_TOKEN", "FREESOUND_API_KEY")


def get_duck() -> str:
    """Fetches a random duck.

    Returns:
        str: The url of the image.

    Raises:
        ValueError: If the response from random-d.uk is not a valid result.
        RuntimeError: If the request to random-d.uk fails due to a timeout or other request-related error.
    """

    try:
        logger.info(f"Fetching random duck from {RANDOM_DUCK_URL}")

        response = requests.get(RANDOM_DUCK_URL, timeout=5)

        # Check if the request was successful
        response.raise_for_status()

        try:
            random_duck_url = loads(response.text)['url']
        except ValueError:
            logger.error(f"Invalid response from random-d.uk: {response.text}")
            raise ValueError(f"Invalid response from random-d.uk: {response.text}")

        logger.debug(f"Received random duck: {random_duck_url}")
        logger.info(f"Successfully fetched random duck")

        return random_duck_url

    except requests.exceptions.Timeout:
        logger.error("Request to random-d.uk timed out.")
        raise RuntimeError("Request to random-d.uk timed out.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to random-d.uk failed: {e}")
        raise RuntimeError(f"Request to random-d.uk failed: {e}")


def get_quack() -> str:
    """Fetches a random quack.

    Returns:
        str: The url of the quack.

    Raises:
        ValueError: If the response from freesound.org is not a valid result.
        RuntimeError: If the request to freesound.org fails due to a timeout or other request-related error.
    """

    try:
        logger.info(f"Fetching random quack from {SOUND_QUACK_URL}")

        # Query Results
        response = requests.get(SOUND_QUACK_URL + "&token=" + SOUND_TOKEN, timeout=5)
        response.raise_for_status()  # Check if the request was successful
        try:
            random_quack_id = choice(loads(response.text)['results'])['id']
        except ValueError:
            logger.error(f"Invalid response from freesound.org: {response.text}")
            raise ValueError(f"Invalid response from freesound.org: {response.text}")

        # Get URL
        response = requests.get("https://freesound.org/apiv2/sounds/" + str(random_quack_id) + "?format=json" + "&token=" + SOUND_TOKEN, timeout=5)
        response.raise_for_status()  # Check if the request was successful
        try:
            random_quack_url = loads(response.text)['previews']['preview-hq-mp3']
        except ValueError:
            logger.error(f"Invalid response from freesound.org: {response.text}")
            raise ValueError(f"Invalid response from freesound.org: {response.text}")

        logger.debug(f"Received random quack: {random_quack_url}")
        logger.info(f"Successfully fetched random quack")

        return random_quack_url

    except requests.exceptions.Timeout:
        logger.error("Request to freesound.org timed out.")
        raise RuntimeError("Request to freesound.org timed out.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request to freesound.org failed: {e}")
        raise RuntimeError(f"Request to freesound.org failed: {e}")
