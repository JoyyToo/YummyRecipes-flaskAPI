import unittest
import json
import jwt
from datetime import datetime, timedelta

from app import app, db

from app.models import Users

from instance.config import app_config
from faker import Faker


class BaseTestCase(unittest.TestCase):
    """Base test case class."""

    def setUp(self):
        self.app = app.config.from_object(app_config['testing'])
        self.fake = Faker()
        self.client = app.test_client
        self.user = {'email': self.fake.email(), 'username': self.fake.name(), 'password':  self.fake.name()}
        self.category = {'name': 'nametrf', 'desc': 'description'}
        self.recipe = {'name': 'meat pie', 'time': '1 hour',
                       'ingredients': '1 tbsp powder', 'procedure': 'stir'}
        self.wrong_user = {'name': 'testuser_wrong', 'email': self.fake.email(),
                           'password': 'testuser_wrong'}
        with app.app_context():

            db.create_all()
            user = Users(username="test_user", email=self.fake.email(), password="test_password")
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.session.commit()

    @staticmethod
    def generate_token(email):
        """Generates access token for a user"""
        # set up a payload with an expiration time
        # iat - issued at
        # exp - expiration time
        # sub - identifies the subject of the token
        payload = {
            'exp': datetime.utcnow() + timedelta(seconds=3),
            'iat': datetime.utcnow(),
            'sub': email
        }

        # create the byte string token using the payload and the SECRET
        jwt_token = jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

        return jwt_token

    def authenticate(self):
        self.client().post('api/v1/auth/register', data=self.user)
        result = self.client().post('api/v1/auth/login', data=self.user)
        return result

    def create_category(self):
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # create a category by making a POST request
        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        return result

    def create_recipe(self):
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # create a category by making a POST request
        self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        result = self.client().post('api/v1/category/1/recipes',
                                    headers=dict(Authorization="Bearer " + jwt_token),
                                    data=self.recipe)
        return result


if __name__ == "__main__":
    unittest.main()
