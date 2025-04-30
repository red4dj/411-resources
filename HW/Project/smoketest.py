import requests


def run_smoketest():
    """Run sequential smoketests."""

    # region BASE
    base_url = "http://localhost:5000/api"
    username = "test"
    password = "test"
    # endregion

    # region HEALTH CHECK
    health_response = requests.get(f"{base_url}/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "success"
    # endregion

    # region RESET
    delete_user_response = requests.delete(f"{base_url}/reset-users")
    assert delete_user_response.status_code == 200
    assert delete_user_response.json()["status"] == "success"
    print("Reset users successful")

    # delete_ducks_response = requests.delete(f"{base_url}/reset-ducks")
    # assert delete_ducks_response.status_code == 200
    # assert delete_ducks_response.json()["status"] == "success"
    # print("Reset ducks successful")

    # delete_favorites_response = requests.delete(f"{base_url}/reset-favorites")
    # assert delete_favorites_response.status_code == 200
    # assert delete_favorites_response.json()["status"] == "success"
    # print("Reset favorites successful")
    # endregion

    # region CREATE USER
    create_user_response = requests.put(f"{base_url}/create-user", json={
        "username": username,
        "password": password
    })
    assert create_user_response.status_code == 201
    assert create_user_response.json()["status"] == "success"
    print("User creation successful")
    # endregion

    # region LOGIN
    session = requests.Session()

    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": password
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login successful")
    # endregion

    # region CHANGE PASSWORD
    change_password_resp = session.post(f"{base_url}/change-password", json={
        "new_password": "new_password"
    })
    assert change_password_resp.status_code == 200
    assert change_password_resp.json()["status"] == "success"
    print("Password change successful")

    login_resp = session.post(f"{base_url}/login", json={
        "username": username,
        "password": "new_password"
    })
    assert login_resp.status_code == 200
    assert login_resp.json()["status"] == "success"
    print("Login with new password successful")
    # endregion

    # region GET DUCK
    get_duck_resp = session.post(f"{base_url}/get-duck")
    assert get_duck_resp.status_code == 201
    assert get_duck_resp.json()["status"] == "success"
    print("Duck got getted")
    # endregion

    # region SAVE DUCK
    get_duck_resp = session.post(f"{base_url}/save-duck")
    assert get_duck_resp.status_code == 201
    assert get_duck_resp.json()["status"] == "success"
    print("A Duck was saved!")
    # endregion

    # region REMOVE DUCK
    get_duck_resp = session.post(f"{base_url}/remove-duck")
    assert get_duck_resp.status_code == 201
    assert get_duck_resp.json()["status"] == "success"
    print("We lost a duck...")
    # endregion

    # region LIST DUCKS
    get_duck_resp = session.post(f"{base_url}/list-ducks")
    assert get_duck_resp.status_code == 201
    assert get_duck_resp.json()["status"] == "success"
    print("Ducks were listed. You're a regular birdwatcher!")
    # endregion

    # region QUACK
    get_duck_resp = session.post(f"{base_url}/quack")
    assert get_duck_resp.status_code == 201
    assert get_duck_resp.json()["status"] == "success"
    print("QUACK!")
    # endregion

    # region LOGOUT
    logout_resp = session.post(f"{base_url}/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("Logout successful")
    # endregion

    # region NO AUTH
    get_duck_logged_out_resp = session.post(f"{base_url}/get-duck")
    # This should fail because we are logged out
    assert get_duck_logged_out_resp.status_code == 401
    assert get_duck_logged_out_resp.json()["status"] == "error"
    print("Duck get failed as expected")
    # endregion


if __name__ == "__main__":
    run_smoketest()
