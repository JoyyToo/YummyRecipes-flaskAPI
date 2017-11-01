import os
from flask import Flask
from flask_restplus import Api, Resource
from flask_sqlalchemy import SQLAlchemy

from instance.config import app_config

app = Flask(__name__)
app.config.from_object(app_config[os.getenv('APP_SETTINGS')])
api = Api(app)
db = SQLAlchemy(app)

from . import views

