import jwt
from datetime import datetime, timedelta
from app import db, app
from flask_bcrypt import Bcrypt


class Users(db.Model):
    """This class defines the users table"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    username = db.Column(db.String(256), nullable=False)
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

    def generate_token(self, user_id):
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
            return "Expired token. Please login to get a new token"
        except jwt.InvalidTokenError:
            # token is invalid
            return "Invalid token. Please register or login"


class Categories(db.Model):
    """This class defines Categories tables."""

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    desc = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(
        db.DateTime, default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey(Users.id))

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

    def save(self):
        """Saves Category to the database"""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all(user_id):
        """Returns all available Categories for a given user."""
        return Categories.query.filter_by(user_id=user_id)

    @staticmethod
    def get_single(id):
        """Returns all available Categories for a given user."""
        return Categories.query.filter_by(id=id).first()

    def delete(self):
        """Deletes a given Category"""
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        """Returns a representation of a Category."""
        return "<Category: {}>".format(self.name)