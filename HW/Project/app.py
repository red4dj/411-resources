from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests  # Add this line
# from flask_cors import CORS

from config import ProductionConfig

from ducks.db import db
from ducks.models.ducks_model import Ducks as Boxers  # Change this line
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
    # Boxers
    #
    ##########################################################

    @app.route('/api/reset-boxers', methods=['DELETE'])
    def reset_boxers() -> Response:
        """Recreate the boxers table to delete boxers users.

        Returns:
            JSON response indicating the success of recreating the Boxers table.

        Raises:
            500 error if there is an issue recreating the Boxers table.
        """
        try:
            app.logger.info("Received request to recreate Boxers table")
            with app.app_context():
                Boxers.__table__.drop(db.engine)
                Boxers.__table__.create(db.engine)
            app.logger.info("Boxers table recreated successfully")
            return make_response(jsonify({
                "status": "success",
                "message": f"Boxers table recreated successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Boxers table recreation failed: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting users",
                "details": str(e)
            }), 500)


    @app.route('/api/add-boxer', methods=['POST'])
    @login_required
    def add_boxer() -> Response:
        """Route to add a new boxer to the gym.

        Expected JSON Input:
            - name (str): The boxer's name.
            - weight (int): The boxer's weight.
            - height (int): The boxer's height.
            - reach (float): The boxer's reach in inches.
            - age (int): The boxer's age.

        Returns:
            JSON response indicating the success of the boxer addition.

        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the boxer to the database.

        """
        app.logger.info("Received request to create new boxer")

        try:
            data = request.get_json()

            required_fields = ["name", "weight", "height", "reach", "age"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                app.logger.warning(f"Missing required fields: {missing_fields}")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400)

            name = data["name"]
            weight = data["weight"]
            height = data["height"]
            reach = data["reach"]
            age = data["age"]

            if (
                not isinstance(name, str)
                or not isinstance(weight, (int, float))
                or not isinstance(height, (int, float))
                or not isinstance(reach, (int, float))
                or not isinstance(age, int)
            ):
                app.logger.warning("Invalid input data types")
                return make_response(jsonify({
                    "status": "error",
                    "message": "Invalid input types: name should be a string, weight/height/reach should be numbers, age should be an integer"
                }), 400)

            app.logger.info(f"Adding boxer: {name}, {weight}kg, {height}cm, {reach} inches, {age} years old")
            Boxers.create_boxer(name, weight, height, reach, age)

            app.logger.info(f"Boxer added successfully: {name}")
            return make_response(jsonify({
                "status": "success",
                "message": f"Boxer '{name}' added successfully"
            }), 201)

        except Exception as e:
            app.logger.error(f"Failed to add boxer: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while adding the boxer",
                "details": str(e)
            }), 500)


    @app.route('/api/delete-boxer/<int:boxer_id>', methods=['DELETE'])
    @login_required
    def delete_boxer(boxer_id: int) -> Response:
        """Route to delete a boxer by ID.

        Path Parameter:
            - boxer_id (int): The ID of the boxer to delete.

        Returns:
            JSON response indicating success of the operation.

        Raises:
            400 error if the boxer does not exist.
            500 error if there is an issue removing the boxer from the database.

        """
        try:
            app.logger.info(f"Received request to delete boxer with ID {boxer_id}")

            # Check if the boxer exists before attempting to delete
            boxer = Boxers.get_boxer_by_id(boxer_id)
            if not boxer:
                app.logger.warning(f"Boxer with ID {boxer_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Boxer with ID {boxer_id} not found"
                }), 400)

            Boxers.delete_boxer(boxer_id)
            app.logger.info(f"Successfully deleted boxer with ID {boxer_id}")

            return make_response(jsonify({
                "status": "success",
                "message": f"Boxer with ID {boxer_id} deleted successfully"
            }), 200)

        except Exception as e:
            app.logger.error(f"Failed to add boxer: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while deleting the boxer",
                "details": str(e)
            }), 500)


    @app.route('/api/get-boxer-by-id/<int:boxer_id>', methods=['GET'])
    @login_required
    def get_boxer_by_id(boxer_id: int) -> Response:
        """Route to get a boxer by its ID.

        Path Parameter:
            - boxer_id (int): The ID of the boxer.

        Returns:
            JSON response containing the boxer details if found.

        Raises:
            400 error if the boxer is not found.
            500 error if there is an issue retrieving the boxer from the database.

        """
        try:
            app.logger.info(f"Received request to retrieve boxer with ID {boxer_id}")

            boxer = Boxers.get_boxer_by_id(boxer_id)

            if not boxer:
                app.logger.warning(f"Boxer with ID {boxer_id} not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Boxer with ID {boxer_id} not found"
                }), 400)

            app.logger.info(f"Successfully retrieved boxer: {boxer}")
            return make_response(jsonify({
                "status": "success",
                "boxer": boxer
            }), 200)

        except Exception as e:
            app.logger.error(f"Error retrieving boxer with ID {boxer_id}: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the boxer",
                "details": str(e)
            }), 500)


    @app.route('/api/get-boxer-by-name/<string:boxer_name>', methods=['GET'])
    @login_required
    def get_boxer_by_name(boxer_name: str) -> Response:
        """Route to get a boxer by its name.

        Path Parameter:
            - boxer_name (str): The name of the boxer.

        Returns:
            JSON response containing the boxer details if found.

        Raises:
            400 error if the boxer name is missing or not found.
            500 error if there is an issue retrieving the boxer from the database.

        """
        try:
            app.logger.info(f"Received request to retrieve boxer with name '{boxer_name}'")

            boxer = Boxers.get_boxer_by_name(boxer_name)

            if not boxer:
                app.logger.warning(f"Boxer '{boxer_name}' not found.")
                return make_response(jsonify({
                    "status": "error",
                    "message": f"Boxer '{boxer_name}' not found"
                }), 400)

            app.logger.info(f"Successfully retrieved boxer: {boxer}")
            return make_response(jsonify({
                "status": "success",
                "boxer": boxer
            }), 200)

        except Exception as e:
            app.logger.error(f"Error retrieving boxer with name '{boxer_name}': {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "An internal error occurred while retrieving the boxer",
                "details": str(e)
            }), 500)


        
    ##########################################################
    #
    # Duck API
    #
    ##########################################################

    @app.route('/api/ducks/random', methods=['GET'])
    @login_required  # Remove this if you want public access
    def get_random_duck() -> Response:
        """Get a random duck image.
        
        Query Parameters:
            - type (optional): Filter for image type ('JPG' or 'GIF')
            
        Returns:
            JSON response with the duck image URL and message.
        """
        image_type = request.args.get('type')
        endpoint = "https://random-d.uk/api/v2/random"
        
        params = {}
        if image_type and image_type.upper() in ["JPG", "GIF"]:
            params["type"] = image_type.upper()
            
        try:
            app.logger.info(f"Fetching random duck image with params: {params}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return make_response(jsonify(response.json()), 200)
        except Exception as e:
            app.logger.error(f"Error fetching random duck: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "Failed to fetch duck image",
                "details": str(e)
            }), 500)

    @app.route('/api/ducks/quack', methods=['GET'])
    @login_required  # Remove this if you want public access
    def get_quack() -> Response:
        """Get a random duck image using the quack endpoint.
        
        Returns:
            JSON response with the duck image URL and message.
        """
        endpoint = "https://random-d.uk/api/v2/quack"
        
        try:
            app.logger.info("Fetching quack duck image")
            response = requests.get(endpoint)
            response.raise_for_status()
            return make_response(jsonify(response.json()), 200)
        except Exception as e:
            app.logger.error(f"Error fetching quack duck: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "Failed to fetch duck image",
                "details": str(e)
            }), 500)

    @app.route('/api/ducks/list', methods=['GET'])
    @login_required  # Remove this if you want public access
    def get_duck_list() -> Response:
        """Get list of all available duck images.
        
        Returns:
            JSON response with lists of images and gifs.
        """
        endpoint = "https://random-d.uk/api/v2/list"
        
        try:
            app.logger.info("Fetching duck image list")
            response = requests.get(endpoint)
            response.raise_for_status()
            return make_response(jsonify(response.json()), 200)
        except Exception as e:
            app.logger.error(f"Error fetching duck list: {e}")
            return make_response(jsonify({
                "status": "error",
                "message": "Failed to fetch duck image list",
                "details": str(e)
            }), 500)

    @app.route('/api/ducks/http/<int:status_code>', methods=['GET'])
    @login_required  # Remove this if you want public access
    def get_http_duck(status_code: int) -> Response:
        """Get a duck image representing an HTTP status code.
        
        Path Parameters:
            - status_code: HTTP status code (100-599)
            
        Returns:
            JSON response with the URL for the HTTP duck image.
        """
        if not isinstance(status_code, int) or status_code < 100 or status_code >= 600:
            app.logger.warning(f"Invalid HTTP status code: {status_code}")
            return make_response(jsonify({
                "status": "error",
                "message": f"Invalid HTTP status code: {status_code}"
            }), 400)
            
        url = f"https://random-d.uk/api/v2/http/{status_code}"
        app.logger.info(f"Returning HTTP {status_code} duck image")
        return make_response(jsonify({
            "status": "success",
            "url": url,
            "message": f"HTTP {status_code} Duck"
        }), 200)

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