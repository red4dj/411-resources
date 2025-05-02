from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# from flask_cors import CORS

from config import ProductionConfig

from ducks.db import db
from ducks.models.ducks_model import Ducks
from ducks.models.favorites_model import FavoritesModel
from ducks.models.user_model import Users
from ducks.utils.logger import configure_logger


def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    configure_logger(app.logger)

    app.config.from_object(config_class)

    db.init_app(app)  # Initialize db with app
    with app.app_context():
        db.create_all()  # Recreate all tables

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.filter_by(username=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        return make_response(jsonify({
            "status": "error",
            "message": "Authentication required"
        }), 401)

    Favorites = FavoritesModel()

    ####################################################
    #
    # Healthchecks
    #
    ####################################################

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.
        """

        app.logger.info("Health check endpoint hit")
        return make_response(jsonify({
            'status': 'success',
            'message': 'Quack!'
        }), 200)

    ##########################################################
    #
    # User Management
    #
    #########################################################

    @app.route('/api/create-user', methods=['PUT'])
    def create_user() -> Response:
        """Register a new user account.

        Expected JSON Input:
            - username (str): The desired username.
            - password (str): The desired password.

        Returns:
            JSON response indicating the success of the user creation.

        Raises:
            400 error if the username or password is missing.
            500 error if there is an issue creating the user in the database.
        """

        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            Users.create_user(username, password)
            return make_response(jsonify({
                "status": "success",
                "message": f"User '{username}' created successfully"
            }), 201)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"User creation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while creating user",
                "details": str(e)
            }), 500)

    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """Authenticate a user and log them in.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The password of the user.

        Returns:
            JSON response indicating the success of the login attempt.

        Raises:
            401 error if the username or password is incorrect.
        """

        try:
            data = request.get_json()
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Username and password are required"
                }), 400)

            if Users.check_password(username, password):
                user = Users.query.filter_by(username=username).first()
                login_user(user)
                return make_response(jsonify({
                    "status": "success",
                    "message": f"User '{username}' logged in successfully"
                }), 200)
            else:
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid username or password"
                }), 401)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 401)
        except Exception as e:
            app.logger.error(f"Login failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred during login",
                "details": str(e)
            }), 500)

    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout() -> Response:
        """Log out the current user.

        Returns:
            JSON response indicating the success of the logout operation.

        """

        logout_user()
        return make_response(jsonify({
            "status": "success",
            "message": "User logged out successfully"
        }), 200)

    @app.route('/api/change-password', methods=['POST'])
    @login_required
    def change_password() -> Response:
        """Change the password for the current user.

        Expected JSON Input:
            - new_password (str): The new password to set.

        Returns:
            JSON response indicating the success of the password change.

        Raises:
            400 error if the new password is not provided.
            500 error if there is an issue updating the password in the database.
        """

        try:
            data = request.get_json()
            new_password = data.get("new_password")

            if not new_password:
                return make_response(jsonify({
                    "status": "error",
                    "message": "New password is required"
                }), 400)

            username = current_user.username
            Users.update_password(username, new_password)
            return make_response(jsonify({
                "status": "success",
                "message": "Password changed successfully"
            }), 200)

        except ValueError as e:
            return make_response(jsonify({
                "status": "error",
                "message": str(e)
            }), 400)
        except Exception as e:
            app.logger.error(f"Password change failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while changing password",
                "details": str(e)
            }), 500)

    @app.route('/api/reset-users', methods=['DELETE'])
    def reset_users() -> Response:
        """Recreate the users table to delete all users.

        Returns:
            JSON response indicating the success of recreating the Users table.

        Raises:
            500 error if there is an issue recreating the Users table.
        """

        try:
            app.logger.info("Received request to recreate Users table")
            with app.app_context():
                Users.__table__.drop(db.engine)
                Users.__table__.create(db.engine)
            app.logger.info("Users table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Users table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Users table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Ducks
    #
    ##########################################################

    @app.route('/api/reset-ducks', methods=['DELETE'])
    def reset_ducks() -> Response:
        """Recreate the ducks table to delete ducks.

        Returns:
            JSON response indicating the success of recreating the Ducks table.

        Raises:
            500 error if there is an issue recreating the Ducks table.
        """

        try:
            app.logger.info("Received request to recreate Ducks table")
            with app.app_context():
                Ducks.__table__.drop(db.engine)
                Ducks.__table__.create(db.engine)
            app.logger.info("Ducks table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": "Ducks table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Ducks table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting ducks",
                "details": str(e)
            }), 500)

    @app.route('/api/get-duck', methods=['GET'])
    @login_required
    def get_duck() -> Response:
        """Route to get a random duck.

        Returns:
            JSON response with the duck image url.

        Raises:
            500 error if there is an issue getting the duck.
        """

        app.logger.info("Received request for new duck")

        try:
            duck = Ducks.create_duck_random()

            app.logger.info(f"Duck added successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Duck added successfully",
                "id": duck.id,
                "url": duck.url
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to get duck: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while getting the duck",
                "details": str(e)
            }), 500)

    @app.route('/api/delete-duck/<int:duck_id>', methods=['DELETE'])
    @login_required
    def delete_duck(duck_id: int) -> Response:
        """Route to delete a duck by ID.

        Path Parameter:
            - duck_id (int): The ID of the duck to delete.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the duck does not exist.
            500 error if there is an issue removing the duck from the database.
        """

        try:
            app.logger.info(f"Received request to delete duck with ID {duck_id}")

            # Check if the duck exists before attempting to delete
            duck = Ducks.get_duck_by_id(duck_id)
            if not duck:
                app.logger.warning(f"Duck with ID {duck_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Duck with ID {duck_id} not found"
                }), 400)

            Ducks.delete_duck(duck_id)
            app.logger.info(f"Successfully deleted duck with ID {duck_id}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Duck with ID {duck_id} deleted successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to delete duck: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting the duck",
                "details": str(e)
            }), 500)

    @app.route('/api/get-duck-by-id/<int:duck_id>', methods=['GET'])
    @login_required
    def get_duck_by_id(duck_id: int) -> Response:
        """Route to get a duck by its ID.

        Path Parameter:
            - duck_id (int): The ID of the duck.

        Returns:
            JSON response containing the duck details if found.

        Raises:
            400 error if the boxer is not found.
            500 error if there is an issue retrieving the boxer from the database.
        """

        try:
            app.logger.info(f"Received request to retrieve duck with ID {duck_id}")

            duck = Ducks.get_duck_by_id(duck_id)

            if not duck:
                app.logger.warning(f"Duck with ID {duck_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Duck with ID {duck_id} not found"
                }), 400)

            app.logger.info(f"Successfully retrieved duck: {duck}")
            return make_response(jsonify({
                "status": "success",
                "id": duck.id,
                "url": duck.url
            }), 200)

        except Exception as e:
            app.logger.error(f"Error retrieving duck with ID {duck_id}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the duck",
                "details": str(e)
            }), 500)

    @app.route('/api/quack', methods=['GET'])
    @login_required
    def quack() -> Response:
        """Route to get a random quack.

        Returns:
            JSON response with the duck quack url.

        Raises:
            500 error if there is an issue getting the duck to quack.
        """

        app.logger.info("Received quack request")

        try:
            url = Ducks.make_duck_quack()

            app.logger.info(f"Duck quacked: {url}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Duck quacked successfully!",
                "url": url
            }), 201)

        except Exception as e:
            app.logger.error("Failed to get duck to quack")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while getting the duck to quack",
                "details": str(e)
            }), 500)

    ##########################################################
    #
    # Favorite Ducks
    #
    ##########################################################

    @app.route('/api/list-ducks', methods=['GET'])
    @login_required
    def list_ducks() -> Response:
        """Route to get list of favorite ducks

        Returns:
            JSON response with the list of ducks.

        Raises:
            500 error if there is an issue getting the ducks.
        """

        try:
            app.logger.info("Retrieving list of favorite ducks...")

            ducks = Favorites.get_ducks()

            for i in range(len(ducks)):
                ducks[i] = {"id": ducks[0].id, "url": ducks[i].url}

            app.logger.info(f"Retrieved {len(ducks)} duck(s).")
            return make_response(jsonify({
                "status": "success",
                "ducks": ducks
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to retrieve ducks: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving ducks",
                "details": str(e)
            }), 500)

    @app.route('/api/favorite-duck', methods=['POST'])
    @login_required
    def add_duck_to_favorites() -> Response:
        """Route to add a duck to list of favorites.

        Expected JSON Input:
            - id (int): The duck's id.

        Returns:
            JSON response indicating the success of the duck being favorite.

        Raises:
            400 error if the request is invalid.
            500 error if there is an issue with the duck being favorite.
        """

        try:
            data = request.get_json()
            duck_id = data.get("id")

            if not duck_id:
                app.logger.warning("Attempted to favorite duck without specifying an id.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "You must provide a duck id"
                }), 400)

            app.logger.info(f"Attempting to favorite duck ID: {duck_id}")

            duck = Ducks.get_duck_by_id(duck_id)

            if not duck:
                app.logger.warning(f"Duck ID {duck_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Duck ID {duck_id} not found."
                }), 400)

            try:
                Favorites.add_duck_to_favorites(duck_id)
            except ValueError as e:
                app.logger.warning(f"Cannot favorite ID: {duck_id}: {e}")
                return make_response(jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400)

            app.logger.info(f"Duck ID {duck_id} added to favorites.")

            return make_response(jsonify({
                "status": "success",
                "message": f"Duck ID {duck_id} added to favorites."
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to add duck to favorites: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the duck to favorites",
                "details": str(e)
            }), 500)

    @app.route('/api/unfavorite-duck', methods=['POST'])
    @login_required
    def remove_duck_from_favorites() -> Response:
        """Route to remove a duck from list of favorites.

        Expected JSON Input:
            - id (int): The duck's id.

        Returns:
            JSON response indicating the success of the duck no longer being favorite.

        Raises:
            400 error if the request is invalid.
            500 error if there is an issue with the duck not being favorite.
        """

        try:
            data = request.get_json()
            duck_id = data.get("id")

            if not duck_id:
                app.logger.warning("Attempted to unfavorite duck without specifying an id.")
                return make_response(jsonify({
                    "status": "error",
                    "message": "You must provide a duck id"
                }), 400)

            app.logger.info(f"Attempting to unfavorite duck ID: {duck_id}")

            duck = Favorites.get_duck_by_duck_id(duck_id)

            if not duck:
                app.logger.warning(f"Duck ID {duck_id} not found in favorites.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Duck ID {duck_id} not found in favorites."
                }), 400)

            try:
                Favorites.remove_duck_by_duck_id(duck_id)
            except ValueError as e:
                app.logger.warning(f"Cannot unfavorite ID: {duck_id}: {e}")
                return make_response(jsonify({
                    "status": "error",
                    "message": str(e)
                }), 400)

            app.logger.info(f"Duck ID {duck_id} removed from favorites.")

            return make_response(jsonify({
                "status": "success",
                "message": f"Duck ID {duck_id} removed from favorites."
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to remove duck from favorites: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while removing the duck from favorites",
                "details": str(e)
            }), 500)

    return app


if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Ducks Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        app.logger.error(f"Flask Ducks encountered a predator: {e}")
    finally:
        app.logger.info("Duck has died.")
