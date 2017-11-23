import unittest

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
                       'ingredients': '1 tbsp powder', 'direction': 'stir'}
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
        req = self.client().post('api/v1/auth/login', data=self.user)
        return req


if __name__ == "__main__":
    unittest.main()
