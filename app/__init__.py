from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from instance.config import app_config
from app.models import User, Categories, Recipes

app = Flask(__name__)

db = SQLAlchemy(app)

app.config.from_object(app_config['staging'])





