import requests


def run_smoketest():
    base_url = "http://localhost:5000/api"
    username = "test"
    password = "test"

    test_muhammad_ali = {
        "name": "Muhammad Ali",
        "weight": 210,
        "height": 191,
        "reach": 78,
        "age": 32
    }

    test_joe_frazier = {
        "name": "Joe Frazier",
        "weight": 205,
        "height": 182,
        "reach": 73,
        "age": 30
    }

    health_response = requests.get(f"{base_url}/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "success"

    delete_user_response = requests.delete(f"{base_url}/reset-users")
    assert delete_user_response.status_code == 200
    assert delete_user_response.json()["status"] == "success"
    print("Reset users successful")

    delete_boxer_response = requests.delete(f"{base_url}/reset-boxers")
    assert delete_boxer_response.status_code == 200
    assert delete_boxer_response.json()["status"] == "success"
    print("Reset boxers successful")

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

    create_boxer_resp = session.post(f"{base_url}/add-boxer", json=test_muhammad_ali)
    assert create_boxer_resp.status_code == 201
    assert create_boxer_resp.json()["status"] == "success"
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

    create_boxer_resp = session.post(f"{base_url}/add-boxer", json=test_joe_frazier)
    assert create_boxer_resp.status_code == 201
    assert create_boxer_resp.json()["status"] == "success"
    print("Boxer creation successful")

    # Log out
    logout_resp = session.post(f"{base_url}/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "success"
    print("Logout successful")

    create_boxer_logged_out_resp = session.post(f"{base_url}/add-boxer", json=test_muhammad_ali)
    # This should fail because we are logged out
    assert create_boxer_logged_out_resp.status_code == 401
    assert create_boxer_logged_out_resp.json()["status"] == "error"
    print("Boxer creation failed as expected")

if __name__ == "__main__":
    run_smoketest()
