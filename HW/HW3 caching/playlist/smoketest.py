import requests


def run_smoketest():
    base_url = "http://localhost:5000/api"
    username = "test"
    password = "test"


    song_beatles = {
        "artist": "The Beatles",
        "title": "Come Together",
        "year": 1969,
        "genre": "Rock",
        "duration": 259
    }

    song_nirvana = {
        "artist": "Nirvana",
        "title": "Smells Like Teen Spirit",
        "year": 1991,
        "genre": "Grunge",
        "duration": 301
    }

    health_response = requests.get(f"{base_url}/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "success"

    delete_user_response = requests.delete(f"{base_url}/reset-users")
    assert delete_user_response.status_code == 200
    assert delete_user_response.json()["status"] == "success"
    print("Reset users successful")

    delete_song_response = requests.delete(f"{base_url}/reset-songs")
    assert delete_song_response.status_code == 200
    assert delete_song_response.json()["status"] == "success"
    print("Reset song successful")

    create_user_response = requests.put(f"{base_url}/create-user", json={
        "username": username,
        "password": password
    })
    assert create_user_response.status_code == 201
    assert create_user_response.json()["status"] == "success"
    print("User creation successful")

    session = requests.Session()

    # Log in
    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": password
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login successful")

    create_song_resp = session.post(f"{base_url}/create-song", json=song_beatles)
    assert create_song_resp.status_code == 201
    assert create_song_resp.json()["status"] == "success"
    print("Boxer creation successful")

    # Change password
    change_password_resp = session.post(f"{base_url}/change-password", json={
        "new_password": "new_password"
    })
    assert change_password_resp.status_code == 200
    assert change_password_resp.json()["status"] == "success"
    print("Password change successful")

    # Log in with new password
    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": "new_password"
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login with new password successful")

    create_boxer_resp = session.post(f"{base_url}/create-song", json=song_nirvana)
    assert create_boxer_resp.status_code == 201
    assert create_boxer_resp.json()["status"] == "success"
    print("Song creation successful")

    # Log out
    logout_resp = session.post(f"{base_url}/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("Logout successful")

    create_boxer_logged_out_resp = session.post(f"{base_url}/create-song", json=song_nirvana)
    # This should fail because we are logged out
    assert create_boxer_logged_out_resp.status_code == 401
    assert create_boxer_logged_out_resp.json()["status"] == "error"
    print("Song creation failed as expected")

if __name__ == "__main__":
    run_smoketest()
