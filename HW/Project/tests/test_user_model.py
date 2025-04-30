import pytest
from ducks.models.user_model import Users

@pytest.fixture
def sample_user():
    return {
        "username": "testuser",
        "password": "securepassword123"
    }

##########################################################
# User Creation
##########################################################

def test_create_user(session, sample_user):
    """Test creating a new user with a unique username."""
    Users.create_user(**sample_user)
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user is not None
    assert user.username == sample_user["username"]
    assert len(user.salt) == 32
    assert len(user.password) == 64

def test_create_duplicate_user(session, sample_user):
    """Test attempting to create a user with a duplicate username."""
    Users.create_user(**sample_user)
    with pytest.raises(ValueError, match="User with username 'testuser' already exists"):
        Users.create_user(**sample_user)

##########################################################
# User Authentication
##########################################################

def test_check_password_correct(session, sample_user):
    """Test checking the correct password."""
    Users.create_user(**sample_user)
    assert Users.check_password(sample_user["username"], sample_user["password"]) is True

def test_check_password_incorrect(session, sample_user):
    """Test checking an incorrect password."""
    Users.create_user(**sample_user)
    assert Users.check_password(sample_user["username"], "wrongpassword") is False

def test_check_password_user_not_found(session):
    """Test checking password for a non-existent user."""
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.check_password("nonexistentuser", "password")

##########################################################
# Update Password
##########################################################

def test_update_password(session, sample_user):
    """Test updating the password for an existing user."""
    Users.create_user(**sample_user)
    new_password = "newpassword456"
    Users.update_password(sample_user["username"], new_password)
    assert Users.check_password(sample_user["username"], new_password) is True

def test_update_password_user_not_found(session):
    """Test updating the password for a non-existent user."""
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.update_password("nonexistentuser", "newpassword")

##########################################################
# Delete User
##########################################################

def test_delete_user(session, sample_user):
    """Test deleting an existing user."""
    Users.create_user(**sample_user)
    Users.delete_user(sample_user["username"])
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user is None

def test_delete_user_not_found(session):
    """Test deleting a non-existent user."""
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.delete_user("nonexistentuser")

##########################################################
# Get User
##########################################################

def test_get_id_by_username(session, sample_user):
    """Test successfully retrieving a user's ID by their username."""
    Users.create_user(**sample_user)
    user_id = Users.get_id_by_username(sample_user["username"])
    user = session.query(Users).filter_by(username=sample_user["username"]).first()
    assert user.id == user_id

def test_get_id_by_username_user_not_found(session):
    """Test failure when retrieving a non-existent user's ID."""
    with pytest.raises(ValueError, match="User nonexistentuser not found"):
        Users.get_id_by_username("nonexistentuser")
