import os
from flask import Flask, current_app
from flask_restplus import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

app = Flask(__name__)
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