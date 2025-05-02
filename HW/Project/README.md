# DUCKS! 🦆
Ducks provides the user with photos of ducks and allows them to save their favorites. Oh... and it quacks...

## APIs
- [Random-d.uk API](https://random-d.uk/api)
- [Freesound API](https://freesound.org/docs/api/overview.html)


## Endpoints

### Healthchecks
#### [/api/health](http://127.0.0.1:5000/api/health)
  - **Request Type:** `GET`
  - **Purpose:** Health check route to verify the service is running.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "message": "Quack!",
      "status": "success"
    }
    ```

### User Management
#### [/api/create-user](http://127.0.0.1:5000/api/create-user)
  - **Request Type:** `PUT`
  - **Purpose:** Register a new user account.
  - **Request Body:**
    - `username`_(str)_: The desired username
    - `password`_(str)_: The desired password
  - **Example Request Body**:
    ```json
    {
      "username": "ducky",
      "password": "quack_quack"
    }
    ```
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "User 'ducky' created successfully"
    }
    ```

#### [/api/login](http://127.0.0.1:5000/api/login)
  - **Request Type:** `POST`
  - **Purpose:** Authenticate a user and log them in.
  - **Request Body:**
    - `username`_(str)_: The username of the user
    - `password`_(str)_: The password of the user
  - **Example Request Body**:
    ```json
    {
      "username": "ducky",
      "password": "quack_quack"
    }
    ```
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "User 'ducky' logged in successfully"
    }
    ```

#### [/api/logout](http://127.0.0.1:5000/api/logout)
  - **Request Type:** `POST`
  - **Purpose:** Log out the current user.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "User logged out successfully"
    }
    ```

#### [/api/change-password](http://127.0.0.1:5000/api/change-password)
  - **Request Type:** `POST`
  - **Purpose:** Change the password for the current user.
  - **Request Body:**
    - `new_password`_(str)_: The new password to set
  - **Example Request Body**:
    ```json
    {
      "new_password": "quack_quack"
    }
    ```
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Password changed successfully"
    }
    ```

#### [/api/reset-users](http://127.0.0.1:5000/api/reset-users)
  - **Request Type:** `DELETE`
  - **Purpose:** Recreate the users table to delete all users.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Users table recreated successfully"
    }
    ```

### Ducks
#### [/api/reset-ducks](http://127.0.0.1:5000/api/reset-ducks)
  - **Request Type:** `DELETE`
  - **Purpose:** Recreate the ducks table to delete ducks.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Ducks table recreated successfully"
    }
    ```

#### [/api/get-duck](http://127.0.0.1:5000/api/get-duck)
  - **Request Type:** `GET`
  - **Purpose:** Route to get a random duck.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "id": 1,
      "message": "Duck added successfully",
      "status": "success",
      "url": "https://random-d.uk/api/1.gif"
    }
    ```

#### [/api/delete-duck/<duck_id>](http://127.0.0.1:5000/api/delete-duck/1)
  - **Request Type:** `DELETE`
  - **Purpose:** Route to delete a duck by ID.
  - **Get Parameters:**
    - `id`_(int)_: The ID of the duck to delete
  - **Example Request URL**: `/api/delete-duck/1`
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Duck with ID 1 deleted successfully"
    }
    ```

#### [/api/get-duck-by-id/<duck_id>](http://127.0.0.1:5000/api/get-duck-by-id/1)
  - **Request Type:** `GET`
  - **Purpose:** Route to get a duck by its ID.
  - **Get Parameters:**
    - `id`_(int)_: The ID of the duck
  - **Example Request URL**: `/api/get-duck-by-id/1`
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "id": 1,
      "status": "success",
      "url": "https://random-d.uk/api/379.jpg"
    }
    ```

#### [/api/quack](http://127.0.0.1:5000/api/quack)
  - **Request Type:** `GET`
  - **Purpose:** Route to get a random quack.
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Duck quacked successfully!",
      "url": "https://cdn.freesound.org/previews/456/456770_9514571-hq.mp3"
    }
    ```

### Favorite Ducks
#### [/api/list-ducks](http://127.0.0.1:5000/api/list-ducks)
  - **Request Type:** `GET`
  - **Purpose:** Route to get list of favorite ducks
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "ducks": [
        {"id": 1, "url": "https://random-d.uk/api/1.jpg"},
        {"id": 2, "url": "https://random-d.uk/api/1.gif"}
      ]
    }
    ```

#### [/api/favorite-duck](http://127.0.0.1:5000/api/favorite-duck)
  - **Request Type:** `POST`
  - **Purpose:** Route to add a duck to list of favorites.
  - **Request Body:**
    - `id`_(int)_: The ID of the duck to favorite
  - **Example Request Body**:
    ```json
    {
      "id": 1
    }
    ```
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Duck ID 1 added to favorites."
    }
    ```

#### [/api/unfavorite-duck](http://127.0.0.1:5000/api/unfavorite-duck)
  - **Request Type:** `POST`
  - **Purpose:** Route to remove a duck from list of favorites.
  - **Request Body:**
    - `id`_(int)_: The ID of the duck to unfavorite
  - **Example Request Body**:
    ```json
    {
      "id": 1
    }
    ```
  - **Response Format:** JSON
  - **Successful Response Example**:
    ```json
    {
      "status": "success",
      "message": "Duck ID 1 removed from favorites."
    }
    ```


## Testing
### Unit Tests Passed
![Unit Tests Passed Screenshot](https://github.com/red4dj/411-resources/blob/a587bcaab69e2574e0789aa1ef3bb975c3bc1a0f/HW/Project/screenshot_unit_tests_passed.png?raw=true)

### Smoketests Passed
![Smoketests Passed Screenshot](https://github.com/red4dj/411-resources/blob/a587bcaab69e2574e0789aa1ef3bb975c3bc1a0f/HW/Project/screenshot_smoketests_passed.png?raw=true)
