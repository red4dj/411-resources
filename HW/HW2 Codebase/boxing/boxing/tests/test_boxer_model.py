from contextlib import contextmanager
import re

import pytest

from boxing.models.boxers_model import *

######################################################
#
#    Fixtures
#
######################################################


def normalize_whitespace(sql_query: str) -> str:
    """
    Replaces escape characters with spaces.

    Args:
        sql_query (str): The SQL query to normalize.

    Returns:
        str: The normalized SQL query.
    """
    return re.sub(r'\s+', ' ', sql_query).strip()


@pytest.fixture
def mock_cursor(mocker):
    """
    Creates mock database connection for tests.

    Returns:
        Mock cursor so we can set expectations per test
    """
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_cursor.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        """
        Yields the mocked connection object
        """
        yield mock_conn

    mocker.patch("boxing.models.boxers_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Add and delete
#
######################################################


def test_create_boxer(mock_cursor):
    """
    Test creating a new boxer in the database.
    """
    create_boxer(name="John Doe", weight=160, height=66, reach=24, age=21)

    expected_query = normalize_whitespace("""
        INSERT INTO boxers (name, weight, height, reach, age)
        VALUES (?, ?, ?, ?, ?)
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call (second element of call_args)
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("John Doe", 160, 66, 24, 21)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_create_boxer_duplicate(mock_cursor):
    """
    Test creating a boxer with a duplicate name (should raise an error).
    """
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: boxers.name")

    with pytest.raises(ValueError, match="Boxer with name 'John Doe' already exists"):
        create_boxer(name="John Doe", weight=160, height=66, reach=24, age=21)


def test_create_boxer_invalid_weight():
    """
    Test error when trying to create a boxer with an invalid weight (e.g., less than 125)
    """
    with pytest.raises(ValueError, match=r"Invalid weight: -10. Must be at least 125."):
        create_boxer(name="John Doe", weight=-10, height=66, reach=24, age=21)

    with pytest.raises(ValueError, match=r"Invalid weight: 80. Must be at least 125."):
        create_boxer(name="John Doe", weight=80, height=66, reach=24, age=21)


def test_create_boxer_invalid_height():
    """
    Test error when trying to create a boxer with an invalid height (e.g., less than 0)
    """
    with pytest.raises(ValueError, match=r"Invalid height: -2. Must be greater than 0."):
        create_boxer(name="John Doe", weight=160, height=-2, reach=24, age=21)


def test_create_boxer_invalid_reach():
    """
    Test error when trying to create a boxer with an invalid reach (e.g., less than 0)
    """
    with pytest.raises(ValueError, match=r"Invalid reach: -2. Must be greater than 0."):
        create_boxer(name="John Doe", weight=160, height=66, reach=-2, age=21)


def test_create_boxer_invalid_age():
    """
    Test error when trying to create a boxer with an invalid age (e.g., not between 18 and 40)
    """
    with pytest.raises(ValueError, match=r"Invalid age: 16. Must be between 18 and 40."):
        create_boxer(name="John Doe", weight=160, height=66, reach=24, age=16)

    with pytest.raises(ValueError, match=r"Invalid age: 50. Must be between 18 and 40."):
        create_boxer(name="John Doe", weight=160, height=66, reach=24, age=50)


def test_delete_boxer(mock_cursor):
    """
    Test deleting a boxer from the database by boxer ID.
    """
    # Simulate the existence of a boxer w/ id=1
    # We can use any value other than None
    mock_cursor.fetchone.return_value = True

    delete_boxer(1)

    expected_select_sql = normalize_whitespace("SELECT id FROM boxers WHERE id = ?")
    expected_delete_sql = normalize_whitespace("DELETE FROM boxers WHERE id = ?")

    # Access both calls to `execute()` using `call_args_list`
    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_delete_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_delete_sql == expected_delete_sql, "The UPDATE query did not match the expected structure."

    # Ensure the correct arguments were used in both SQL queries
    expected_select_args = (1,)
    expected_delete_args = (1,)

    actual_select_args = mock_cursor.execute.call_args_list[0][0][1]
    actual_delete_args = mock_cursor.execute.call_args_list[1][0][1]

    assert actual_select_args == expected_select_args, f"The SELECT query arguments did not match. Expected {expected_select_args}, got {actual_select_args}."
    assert actual_delete_args == expected_delete_args, f"The UPDATE query arguments did not match. Expected {expected_delete_args}, got {actual_delete_args}."


def test_delete_boxer_bad_id(mock_cursor):
    """
    Test error when trying to delete a non-existent boxer.
    """
    # Simulate that no boxer exists with the given ID
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found."):
        delete_boxer(999)


######################################################
#
#    Get Boxer
#
######################################################


def test_get_boxer_by_id(mock_cursor):
    """
    Test getting a boxer by id.
    """
    mock_cursor.fetchone.return_value = (1, "John Doe", 160, 66, 24, 21)

    result = get_boxer_by_id(1)

    expected_result = Boxer(1, "John Doe", 160, 66, 24, 21)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = (1,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_id_bad_id(mock_cursor):
    """
    Test error when getting a non-existent boxer.
    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer with ID 999 not found"):
        get_boxer_by_id(999)


def test_get_boxer_by_name(mock_cursor):
    """
    Test getting a boxer by name.
    """
    mock_cursor.fetchone.return_value = (1, "John Doe", 160, 66, 24, 21)

    result = get_boxer_by_name("John Doe")

    expected_result = Boxer(1, "John Doe", 160, 66, 24, 21)

    assert result == expected_result, f"Expected {expected_result}, got {result}"

    expected_query = normalize_whitespace("SELECT id, name, weight, height, reach, age FROM boxers WHERE name = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("John Doe",)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_get_boxer_by_name_bad_name(mock_cursor):
    """
    Test error when getting a non-existent boxer by name.
    """
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Boxer 'Jane Doe' not found."):
        get_boxer_by_name("Jane Doe")


def test_get_leaderboard_wins(mock_cursor):
    """
    Test retrieving leaderboard by wins.
    """
    mock_cursor.fetchall.return_value = [
        (2, "Jane Doe", 150, 63, 22, 20, 3, 2, 0.67),
        (1, "John Doe", 160, 66, 24, 21, 1, 1, 1),
    ]

    boxers = get_leaderboard()

    expected_result = [
        {"id": 2, "name": "Jane Doe", "weight": 150, "height": 63, "reach": 22, "age": 20, "weight_class": "LIGHTWEIGHT", "fights": 3, "wins": 2, "win_pct": 67},
        {"id": 1, "name": "John Doe", "weight": 160, "height": 66, "reach": 24, "age": 21, "weight_class": "LIGHTWEIGHT", "fights": 1, "wins": 1, "win_pct": 100},
    ]

    assert boxers == expected_result, f"Expected {expected_result}, but got {boxers}"

    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


def test_get_leaderboard_win_pct(mock_cursor):
    """
    Test retrieving leaderboard by win_pct.
    """
    mock_cursor.fetchall.return_value = [
        (1, "John Doe", 160, 66, 24, 21, 1, 1, 1),
        (2, "Jane Doe", 150, 63, 22, 20, 3, 2, 0.67),
    ]

    boxers = get_leaderboard("win_pct")

    expected_result = [
        {"id": 1, "name": "John Doe", "weight": 160, "height": 66, "reach": 24, "age": 21, "weight_class": "LIGHTWEIGHT", "fights": 1, "wins": 1, "win_pct": 100},
        {"id": 2, "name": "Jane Doe", "weight": 150, "height": 63, "reach": 22, "age": 20, "weight_class": "LIGHTWEIGHT", "fights": 3, "wins": 2, "win_pct": 67},
    ]

    assert boxers == expected_result, f"Expected {expected_result}, but got {boxers}"

    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0 ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


def test_get_leaderboard_empty_catalog(mock_cursor, caplog):
    """
    Test that retrieving leaderboard returns an empty list when the database is empty and logs a warning.
    """
    mock_cursor.fetchall.return_value = []

    result = get_leaderboard()

    assert result == [], f"Expected empty list, but got {result}"

    assert "The boxers database is empty." in caplog.text, "Expected warning about empty catalog not found in logs."

    expected_query = normalize_whitespace("""
        SELECT id, name, weight, height, reach, age, fights, wins,
               (wins * 1.0 / fights) AS win_pct
        FROM boxers
        WHERE fights > 0 ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."


######################################################
#
#    Stats
#
######################################################


def test_update_boxer_stats_win(mock_cursor):
    """
    Test updating a boxer's stats with a win.
    """
    mock_cursor.fetchone.return_value = True

    boxer_id = 1
    update_boxer_stats(boxer_id, "win")

    expected_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]
    expected_arguments = (boxer_id,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."


def test_update_boxer_stats_loss(mock_cursor):
    """
    Test updating a boxer's stats with a loss.
    """
    mock_cursor.fetchone.return_value = True

    boxer_id = 1
    update_boxer_stats(boxer_id, "loss")

    expected_query = normalize_whitespace("UPDATE boxers SET fights = fights + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    actual_arguments = mock_cursor.execute.call_args_list[1][0][1]
    expected_arguments = (boxer_id,)

    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."
