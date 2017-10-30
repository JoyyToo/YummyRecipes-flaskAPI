"""Models for data"""

from app import db


class User(db.Model):
    """defines user model"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp())
    categories = db.relationship('Categories', order_by='Categories.id', cascade='all, delete-orphan')


class Categories(db.Model):
    """defines categories model"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, foreign_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(100))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp())
    recipes = db.relationship('Recipes', order_by='Recipes.id', cascade='all, delete-orphan')


class Recipes(db.Model):
    """defines recipes model"""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, foreign_key=True)
    category_id = db.Column(db.Integer, foreign_key=True)
    name = db.Column(db.String(50), unique=True)
    time = db.Column(db.varchar(50))
    ingredients = db.Column(db.varchar(200))
    direction = db.Column(db.varchar(200))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp())

