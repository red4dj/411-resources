from dataclasses import dataclass
import logging
import sqlite3
from typing import Any, List

from boxing.utils.sql_utils import get_db_connection
from boxing.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Boxer:
    """
    Initialize a new boxer model and automatically assign weight class
    """
    id: int
    name: str
    weight: int
    height: int
    reach: float
    age: int
    weight_class: str = None

    def __post_init__(self):
        self.weight_class = get_weight_class(self.weight)  # Automatically assign weight class


def create_boxer(name: str, weight: int, height: int, reach: float, age: int) -> None:
    """
    Creates a new boxer in the boxers table.

    Args:
        name (str): Name of the boxer.
        weight (int): Weight of the boxer.
        height (int): Height of the boxer.
        reach (float): Reach of the boxer in inches.
        age (int): Age of the boxer.

    Raises:
        ValueError: If any field is invalid.
        sqlite3.IntegrityError: If any boxer with that name already exists.
        sqlite3.Error: For any other database errors.
    """
    logger.info(f"Received request to create boxer: {name} - Weight: {weight}, Height: {height}, Reach: {reach}, Age: {age}")

    if weight < 125:
        logger.warning(f"Invalid weight: {weight}. Must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Must be at least 125.")
    if height <= 0:
        logger.warning(f"Invalid height: {height}. Must be greater than 0.")
        raise ValueError(f"Invalid height: {height}. Must be greater than 0.")
    if reach <= 0:
        logger.warning(f"Invalid reach: {reach}. Must be greater than 0.")
        raise ValueError(f"Invalid reach: {reach}. Must be greater than 0.")
    if not (18 <= age <= 40):
        logger.warning(f"Invalid age: {age}. Must be between 18 and 40.")
        raise ValueError(f"Invalid age: {age}. Must be between 18 and 40.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if the boxer already exists (name must be unique)
            cursor.execute("SELECT 1 FROM boxers WHERE name = ?", (name,))
            if cursor.fetchone():
                logger.error(f"Boxer already exists: {name}")
                raise ValueError(f"Boxer with name '{name}' already exists")

            cursor.execute("""
                INSERT INTO boxers (name, weight, height, reach, age)
                VALUES (?, ?, ?, ?, ?)
            """, (name, weight, height, reach, age))

            conn.commit()

            logger.info(f"Boxer successfully added: '{name}'")

    except sqlite3.IntegrityError:
        logger.error(f"Boxer already exists: {name}")
        raise ValueError(f"Boxer with name '{name}' already exists")

    except sqlite3.Error as e:
        logger.error(f"Database error while creating boxer: {e}")
        raise e


def delete_boxer(boxer_id: int) -> None:
    """
    Deletes a boxer with the specified id from the boxers table.

    Args:
        boxer_id (int): ID of the boxer.

    Raises:
        ValueError: If boxer with the specified ID is not found.
        sqlite3.Error: For any other database errors.
    """
    logger.info(f"Received request to delete boxer - ID: {boxer_id}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.warning(f"Boxer not found - ID: {boxer_id}")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            cursor.execute("DELETE FROM boxers WHERE id = ?", (boxer_id,))
            conn.commit()

            logger.info(f"Boxer successfully deleted - ID: {boxer_id}")

    except sqlite3.Error as e:
        logger.error(f"Database error while deleting boxer: {e}")
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[dict[str, Any]]:
    """
    Retrieves all boxers who have had more than one fight and sorts in the specified order.

    Args:
        sort_by (str, optional): If "wins", retrieve boxers in order of greatest number of wins.
                                 If "win_pct", retrieve boxers in order of greatest win percentage.

    Returns:
        list[dict]: A list of dictionaries representing all boxers with more than one fight.

    Raises:
        ValueError: If sort_by is not "wins" or "wins_pct".
        sqlite3.Error: If any database error occurs.
    """
    logger.info(f"Received request for leaderboard sorted by {sort_by}")

    query = """
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error(f"Invalid sort_by parameter: {sort_by}")
        raise ValueError(f"Invalid sort_by parameter: {sort_by}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        if not rows:
            logger.warning("The boxers database is empty.")
            return []

        leaderboard = []
        for row in rows:
            logger.info(f"Received row: {row}")

            boxer = {
                'id': row[0],
                'name': row[1],
                'weight': row[2],
                'height': row[3],
                'reach': row[4],
                'age': row[5],
                'weight_class': get_weight_class(row[2]),  # Calculate weight class
                'fights': row[6],
                'wins': row[7],
                'win_pct': round(row[8] * 100, 1)  # Convert to percentage
            }
            leaderboard.append(boxer)

        logger.info(f"Retrieved leaderboard: {leaderboard}")

        return leaderboard

    except sqlite3.Error as e:
        logger.error(f"Database error while retrieving leaderboard: {e}")
        raise e


def get_boxer_by_id(boxer_id: int) -> Boxer:
    """
    Retrieves a boxer from the database by their boxer ID.

    Args:
        boxer_id (int): The ID of the boxer to retrieve.

    Returns:
        Boxer: The Boxer object corresponding to the boxer_id.

    Raises:
        ValueError: If the boxer is not found.
        sqlite3.Error: If any database error occurs.
    """
    logger.info(f"Received request for boxer - ID: {boxer_id}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE id = ?
            """, (boxer_id,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Boxer found - ID: {boxer_id}, Name: {boxer.name}")
                return boxer
            else:
                logger.info(f"Boxer not found - ID: {boxer_id}")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error while retrieving boxer: {e}")
        raise e


def get_boxer_by_name(boxer_name: str) -> Boxer:
    """
    Retrieves a boxer from the database by their name.

    Args:
        boxer_name (str): The name of the boxer.

    Returns:
        Boxer: The Boxer object corresponding to the boxer_name.

    Raises:
        ValueError: If the boxer is not found.
        sqlite3.Error: If any database error occurs.

    """
    logger.info(f"Received request for boxer: {boxer_name}")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, weight, height, reach, age
                FROM boxers WHERE name = ?
            """, (boxer_name,))

            row = cursor.fetchone()

            if row:
                boxer = Boxer(
                    id=row[0], name=row[1], weight=row[2], height=row[3],
                    reach=row[4], age=row[5]
                )
                logger.info(f"Boxer found - ID: {boxer.id}, Name: {boxer_name}")
                return boxer
            else:
                logger.info(f"Boxer not found: {boxer_name}")
                raise ValueError(f"Boxer '{boxer_name}' not found.")

    except sqlite3.Error as e:
        logger.error(f"Database error while retrieving boxer: {e}")
        raise e


def get_weight_class(weight: int) -> str:
    """
    Returns the weight class for a specified weight.

    Args:
        weight (int): The weight of the boxer.

    Returns:
        str: The corresponding weight class for the specified weight.

    Raises:
        ValueError: If weight is less than 125.
    """
    logger.info(f"Received request for weight class of {weight}")

    if weight >= 203:
        weight_class = 'HEAVYWEIGHT'
    elif weight >= 166:
        weight_class = 'MIDDLEWEIGHT'
    elif weight >= 133:
        weight_class = 'LIGHTWEIGHT'
    elif weight >= 125:
        weight_class = 'FEATHERWEIGHT'
    else:
        logger.error(f"Invalid weight: {weight}. Weight must be at least 125.")
        raise ValueError(f"Invalid weight: {weight}. Weight must be at least 125.")

    logger.info(f"Weight class of {weight} calculated: {weight_class}")

    return weight_class


def update_boxer_stats(boxer_id: int, result: str) -> None:
    """
    Updates the stats of a boxer by boxer ID based on a win or loss.

    Args:
        boxer_id (int): The ID of the boxer to update.
        result (string): "win" or "loss".

    Raises:
        ValueError: If the result is not "win" or "loss".
        ValueError: If the boxer is not found.
        sqlite3.Error: If any database error occurs.
    """
    logger.info(f"Received request to update boxer stats - ID: {boxer_id}, Result: {result}")

    if result not in {'win', 'loss'}:
        logger.error(f"Invalid result: {result}. Expected 'win' or 'loss'.")
        raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM boxers WHERE id = ?", (boxer_id,))
            if cursor.fetchone() is None:
                logger.error(f"Boxer not found - ID: {boxer_id}")
                raise ValueError(f"Boxer with ID {boxer_id} not found.")

            if result == 'win':
                cursor.execute("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?", (boxer_id,))
            else:  # result == 'loss'
                cursor.execute("UPDATE boxers SET fights = fights + 1 WHERE id = ?", (boxer_id,))

            conn.commit()

            logger.info(f"Successfully updated boxer stats - ID: {boxer_id}, Result: {result}")

    except sqlite3.Error as e:
        logger.error(f"Database error while updating boxer stats: {e}")
        raise e
