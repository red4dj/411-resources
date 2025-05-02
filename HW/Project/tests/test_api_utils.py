import pytest
import requests

from ducks.utils.api_utils import get_duck, get_quack, RANDOM_DUCK_URL, SOUND_TOKEN, SOUND_QUACK_URL

GET_DUCK_RESPONSE = '{"message":"Powered by random-d.uk","url":"https://random-d.uk/api/1.jpg"}'
GET_QUACK_RESPONSE_1 = ('{"results":[{"id":719113,"name":"Duck Quacking Quietly Twice","tags":["duck","female","quack","quacking","quietly","twice"],'
                        '"license":"http://creativecommons.org/publicdomain/zero/1.0/","username":"OwennewO"}]}')
GET_QUACK_RESPONSE_2 = ('{"id":719113,"url":"https://freesound.org/people/OwennewO/sounds/719113/","name":"Duck Quacking Quietly Twice",'
                        '"download":"https://freesound.org/apiv2/sounds/719113/download/",'
                        '"previews":{"preview-hq-mp3":"https://cdn.freesound.org/previews/719/719113_11244040-hq.mp3",'
                        '"preview-hq-ogg":"https://cdn.freesound.org/previews/719/719113_11244040-hq.ogg",'
                        '"preview-lq-mp3":"https://cdn.freesound.org/previews/719/719113_11244040-lq.mp3",'
                        '"preview-lq-ogg":"https://cdn.freesound.org/previews/719/719113_11244040-lq.ogg"}}')


# GET_DUCK

@pytest.fixture
def mock_get_duck(mocker):
    """Mock get_duck request"""
    # Patch the requests.get call
    # requests.get returns an object, which we have replaced with a mock object
    mock_response = mocker.Mock()
    # We are giving that object a text attribute
    mock_response.text = GET_DUCK_RESPONSE
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response


def test_get_duck(mock_get_duck):
    """Test retrieving a random duck from random-d.uk."""

    result = get_duck()

    # Assert that the result is the mocked random duck
    assert result == "https://random-d.uk/api/1.jpg", f"Expected url \"https://random-d.uk/api/1.jpg\", but got {result}"

    # Ensure that the correct URL was called
    requests.get.assert_called_once_with(RANDOM_DUCK_URL, timeout=5)


def test_get_duck_request_failure(mocker):
    """Test handling of a request failure when calling random-d.uk."""
    # Simulate a request failure
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random-d.uk failed: Connection error"):
        get_duck()


def test_get_duck_timeout(mocker):
    """Test handling of a timeout when calling random-d.uk."""
    # Simulate a timeout
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random-d.uk timed out."):
        get_duck()


def test_get_duck_invalid_response(mock_get_duck):
    """Test handling of an invalid response from random-d.uk."""
    # Simulate an invalid response (non-digit)
    mock_get_duck.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from random-d.uk: invalid_response"):
        get_duck()


# GET_QUACK

@pytest.fixture
def mock_get_quack(mocker):
    """Mock get_quack request"""
    mock_response_1 = mocker.Mock()
    mock_response_1.text = GET_QUACK_RESPONSE_1
    mock_response_2 = mocker.Mock()
    mock_response_2.text = GET_QUACK_RESPONSE_2
    mocker.patch("requests.get", side_effect=[mock_response_1, mock_response_2])
    return mock_response_1


def test_get_quack(mock_get_quack):
    """Test retrieving a random quack from freesound.org."""

    result = get_quack()

    # Assert that the result is the mocked random quack
    url = "https://cdn.freesound.org/previews/719/719113_11244040-hq.mp3"
    assert result == url, f"Expected url \"{url}\", but got {result}"


def test_get_quack_request_failure(mocker):
    """Test handling of a request failure when calling freesound.org."""
    # Simulate a request failure
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to freesound.org failed: Connection error"):
        get_quack()


def test_get_quack_timeout(mocker):
    """Test handling of a timeout when calling freesound.org."""
    # Simulate a timeout
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to freesound.org timed out."):
        get_quack()


def test_get_quack_invalid_response(mock_get_quack):
    """Test handling of an invalid response from freesound.org."""
    # Simulate an invalid response (non-digit)
    mock_get_quack.text = "invalid_response"

    with pytest.raises(ValueError, match="Invalid response from freesound.org: invalid_response"):
        get_quack()
