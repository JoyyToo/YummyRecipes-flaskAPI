import os
from flask import Flask
from flask_restplus import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from instance.config import app_config
from app.error_handler import JsonExceptionHandler

app = Flask(__name__)

CELERY_BROKER_URL = 'redis://localhost:6379',
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
DEBUG = True
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
SECRET_KEY = os.getenv('SECRET_KEY')

app.config.from_object(app_config[os.getenv('APP_SETTINGS')])
authorization = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(app, version='1.0',
          authorizations=authorization,
          title='Yummy Recipe RESTful API',
          description='Yummy Recipes RESTful API with Endpoints.',
          prefix='/api/v1')
db = SQLAlchemy(app)
from . import views
JsonExceptionHandler(app)


