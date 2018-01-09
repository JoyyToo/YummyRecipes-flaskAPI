import jwt
from datetime import datetime, timedelta
from app import db, app
from flask_bcrypt import Bcrypt
import re

INVALID_CHAR = re.compile(r"[<>/{}[\]~`*!@#$%^&()=+]")


class Users(db.Model):
    """This class defines the users table"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), nullable=False, unique=True)
    username = db.Column(db.String(40), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    categories = db.relationship(
        'Categories', order_by='Categories.id', cascade='all, delete-orphan')

    def __init__(self, email, username, password):
        """Initialize user with email and password"""
        self.email = email
        self.username = username
        self.password = Bcrypt().generate_password_hash(password).decode()

    def password_is_valid(self, password):
        """Validate password against its hash"""
        return Bcrypt().check_password_hash(self.password, password)

    def save(self):
        """Saves a user to the database"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def generate_token(user_id):
        """Generates access token for a user"""
        try:
            # set up a payload with an expiration time
            # iat - issued at
            # exp - expiration time
            # sub - identifies the subject of the token
            payload = {
                'exp': datetime.utcnow() + timedelta(hours=24),
                'iat': datetime.utcnow(),
                'sub': user_id
            }

            # create the byte string token using the payload and the SECRET
            jwt_token = jwt.encode(
                payload,
                app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )

            return jwt_token

        except Exception as e:

            # returns an error in string format if an exception occurs.
            return str(e)

    @staticmethod
    def decode_token(token):
        """Decodes the access token from Authorization header."""

        try:
            # try to decode the token using SECRET
            payload = jwt.decode(token, app.config.get('SECRET_KEY'))
            return payload['sub']
        except jwt.ExpiredSignatureError:
            # token is valid but expired
            return {
                       "message": "Expired token. Please login to get a new token",
                       "status": "error"
                   }, 403
        except jwt.InvalidTokenError:
            # token is invalid
            return {
                       "message": "Invalid token. Please register or login",
                       "status": "error"
                   }, 403


class Categories(db.Model):
    """This class defines Categories tables."""

    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    desc = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime, default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id))
    recipes = db.relationship(
        'Recipes', order_by='Recipes.id', cascade='all, delete-orphan')

    def __init__(self, name, desc, user_id):
        """Initialize Categories with name, desc and user_id"""
        self.name = name
        self.desc = desc
        self.user_id = user_id

    @staticmethod
    def update(name, desc, id):
        category = Categories.query.filter_by(id=id).first()
        category.name = name
        category.desc = desc
        category.save()
        return category

    def save(self):
        """Saves Category to the database"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all(user_id):
        """Returns all available Categories for a given user."""
        return Categories.query.filter_by(user_id=user_id)

    @staticmethod
    def get_single(_id):
        """Returns all available Categories for a given user."""
        return Categories.query.filter_by(id=_id).first()

    def delete(self):
        """Deletes a given Category"""
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def validate_input(**kwargs):
        if kwargs:
            for key in kwargs:
                if INVALID_CHAR.search(kwargs[key]):
                    return key

    def __repr__(self):
        """Returns a representation of a Category."""
        return "<Category: {}>".format(self.name)


class Recipes(db.Model):
    """This class defines recipes table"""

    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    time = db.Column(db.String(30))
    ingredients = db.Column(db.String(256))
    procedure = db.Column(db.String(256))
    category_id = db.Column(db.Integer, db.ForeignKey(Categories.id))
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime, default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())

    def __init__(self, name, time, ingredients, procedure, category_id, user_id):
        """Initialize Recipes with name, time, ingredient, procedure, category_id"""

        self.name = name
        self.time = time
        self.ingredients = ingredients
        self.procedure = procedure
        self.category_id = category_id
        self.user_id = user_id

    def save(self):
        """Saves Recipes to the database"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def update(name, time, ingredients, procedure, _id):
        """Updates an existing recipe"""
        recipe = Recipes.query.filter_by(id=_id).first()
        recipe.name = name
        recipe.time = time
        recipe.ingredients = ingredients
        recipe.procedure = procedure
        recipe.save()
        return recipe

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def get_all(category_id):
        """Returns all recipes belonging to a Category"""
        return Recipes.query.filter_by(category_id=category_id).all()

    @staticmethod
    def get_single(_id, category_id):
        """Returns a single recipe by with id = _id"""
        return Recipes.query.filter_by(id=_id, category_id=category_id).first()

    def __repr__(self):
        """Returns an instance of Recipe"""
        return "<Recipe: {}>".format(self.id)


class Sessions(db.Model):
    """This class defines the session table"""

    __tablename__ = "user_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    is_logged_in = db.Column(db.Boolean, default=False)

    def __init__(self, user_id):
        self.user_id = user_id

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def login(user_id):
        session = Sessions.query.filter_by(user_id=user_id).first()
        if session:
            session.is_logged_in = True
            session.save()
            return True
        return False

    @staticmethod
    def logout(user_id):
        session = Sessions.query.filter_by(user_id=user_id).first()
        if session:
            session.is_logged_in = False
            session.save()
            return True
        return False

    @staticmethod
    def login_status(user_id):
        session = Sessions.query.filter_by(user_id=user_id).first()
        if session:
            status = session.is_logged_in
            return status

        return False
