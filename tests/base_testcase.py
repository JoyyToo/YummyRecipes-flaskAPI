import unittest
import json

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

    def authenticate(self):
        self.client().post('api/v1/auth/register', data=self.user)
        result = self.client().post('api/v1/auth/login', data=self.user)
        return result

    def authenticate_and_create_category(self):
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # create a category by making a POST request
        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        self.assertEqual(result.status_code, 201)
        return jwt_token

    def authenticate_create_and_get_category(self):
        result = self.authenticate()

        jwt_token = self.authenticate_and_create_category()

        results = json.loads(result.data.decode())
        return jwt_token

    def authenticate_and_create_recipe(self):
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

        self.assertEqual(result.status_code, 201)
        self.assertIn('Recipe added successfully', str(result.data))
        return jwt_token

    def authenticate_create_and_get_recipe(self):
        result = self.authenticate()

        jwt_token = self.authenticate_and_create_recipe()
        results = json.loads(result.data.decode())
        return jwt_token


if __name__ == "__main__":
    unittest.main()
