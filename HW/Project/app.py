from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests  # Add this line
# from flask_cors import CORS

from config import ProductionConfig

from ducks.db import db
from ducks.models.ducks_model import Ducks
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


    ####################################################
    #
    # Healthchecks
    #
    ####################################################

    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """
        Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.

        """
        app.logger.info("Health check endpoint hit")
        return make_response(jsonify({
            'status': 'success',
            'message': 'Service is running'
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
            url = Ducks.create_duck()

            app.logger.info(f"Duck added successfully: {url}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Duck '{url}' added successfully"
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


    # @app.route('/api/get-boxer-by-id/<int:boxer_id>', methods=['GET'])
    # @login_required
    # def get_boxer_by_id(boxer_id: int) -> Response:
    #     """Route to get a boxer by its ID.
    #
    #     Path Parameter:
    #         - boxer_id (int): The ID of the boxer.
    #
    #     Returns:
    #         JSON response containing the boxer details if found.
    #
    #     Raises:
    #         400 error if the boxer is not found.
    #         500 error if there is an issue retrieving the boxer from the database.
    #
    #     """
    #     try:
    #         app.logger.info(f"Received request to retrieve boxer with ID {boxer_id}")
    #
    #         boxer = Boxers.get_boxer_by_id(boxer_id)
    #
    #         if not boxer:
    #             app.logger.warning(f"Boxer with ID {boxer_id} not found.")
    #             return make_response(jsonify({
    #                 "status": "error",
    #                 "message": f"Boxer with ID {boxer_id} not found"
    #             }), 400)
    #
    #         app.logger.info(f"Successfully retrieved boxer: {boxer}")
    #         return make_response(jsonify({
    #             "status": "success",
    #             "boxer": boxer
    #         }), 200)
    #
    #     except Exception as e:
    #         app.logger.error(f"Error retrieving boxer with ID {boxer_id}: {e}")
    #         return make_response(jsonify({
    #             "status": "error",
    #             "message": "An internal error occurred while retrieving the boxer",
    #             "details": str(e)
    #         }), 500)


    # @app.route('/api/get-boxer-by-name/<string:boxer_name>', methods=['GET'])
    # @login_required
    # def get_boxer_by_name(boxer_name: str) -> Response:
    #     """Route to get a boxer by its name.
    #
    #     Path Parameter:
    #         - boxer_name (str): The name of the boxer.
    #
    #     Returns:
    #         JSON response containing the boxer details if found.
    #
    #     Raises:
    #         400 error if the boxer name is missing or not found.
    #         500 error if there is an issue retrieving the boxer from the database.
    #
    #     """
    #     try:
    #         app.logger.info(f"Received request to retrieve boxer with name '{boxer_name}'")
    #
    #         boxer = Boxers.get_boxer_by_name(boxer_name)
    #
    #         if not boxer:
    #             app.logger.warning(f"Boxer '{boxer_name}' not found.")
    #             return make_response(jsonify({
    #                 "status": "error",
    #                 "message": f"Boxer '{boxer_name}' not found"
    #             }), 400)
    #
    #         app.logger.info(f"Successfully retrieved boxer: {boxer}")
    #         return make_response(jsonify({
    #             "status": "success",
    #             "boxer": boxer
    #         }), 200)
    #
    #     except Exception as e:
    #         app.logger.error(f"Error retrieving boxer with name '{boxer_name}': {e}")
    #         return make_response(jsonify({
    #             "status": "error",
    #             "message": "An internal error occurred while retrieving the boxer",
    #             "details": str(e)
    #         }), 500)

    @app.route('/api/ducks/favorites', methods=['GET'])
    @login_required
    def get_favorite_ducks() -> Response:
        """Get all favorite duck images for the current user.
        
        Returns:
            JSON response with list of favorite duck URLs.
        """
        # This is a placeholder - your teammates will implement the model
        # For now, just return an empty list
        app.logger.info("Returning favorite ducks (placeholder)")
        return make_response(jsonify({
            "status": "success",
            "favorites": []
        }), 200)

    return app  # This is the end of the create_app function

if __name__ == '__main__':
    app = create_app()
    app.logger.info("Starting Ducks Flask app...")
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        app.logger.error(f"Flask app encountered a quack: {e}")
    finally:
        app.logger.info("Flask app has stopped.")