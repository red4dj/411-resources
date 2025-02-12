from flask import Flask, make_response, request
from os import getenv

app = Flask(__name__)


@app.route('/')
def hello():
    response = make_response(
        {
            'response': 'Hello, World!',
            'status': 200
        }
    )
    return response


@app.route('/repeat')
def repeat():
    response = make_response(
        {
            'response': request.args['input'],
            'status': 200
        }
    )
    return response


@app.route('/health')
@app.route('/healthcheck')
def health():
    response = make_response(
        {
            'response': 'OK',
            'status': 200
        }
    )
    return response


@app.route('/hang')
def hang():
    while True:
        pass


if __name__ == '__main__':
    # By default, flask is only accessible from localhost.
    # Set this to '0.0.0.0' to make it accessible from any IP address
    # on your network (not recommended for production use)
    app.run(host='0.0.0.0', port=getenv('PORT'), debug=True, threaded=False)
