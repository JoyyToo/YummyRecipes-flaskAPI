from flask import jsonify
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException


class JsonExceptionHandler(object):
    """
    This class Handles Http errors
    :returns: json object
    """
    def __init__(self, app):
        """
        Initialize the app to handle incoming errors
        :param app: Flask app
        """
        self.init_app(app)

    def std_handler(self, error):
        """
        :param error: error message
        :return: Json object version of the error
        """
        response = jsonify(message=str(error))
        response.status_code = error.code if isinstance(error, HTTPException) else 500
        return response

    def init_app(self, app):
        self.app = app
        self.register(HTTPException)
        for code, v in default_exceptions.items():
            self.register(code)

    def register(self, exception_or_code, handler=None):
        self.app.errorhandler(exception_or_code)(handler or self.std_handler)