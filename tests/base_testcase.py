import unittest, os

from app import app, db

from app.models import Categories, Users, Recipes

from instance.config import app_config


class BaseTestCase(unittest.TestCase):
    """Base test case class."""

    def setUp(self):
        self.app = app.config.from_object(app_config[os.getenv('APP_SETTINGS')])
        self.client = app.test_client
        self.user = {'name': 'testuser', 'email': 'testuser@mail.com', 'password': 'testuser'}
        self.wrong_user = {'name': 'testuser_wrong', 'email': 'testuser_wrong@mail.com',
                           'password': 'testuser_wrong'}

        with app.app_context():
            db.create_all()
            user = Users(username="test_user", email='test_user@mail.com', password="test_password")
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
            db.session.commit()

    def authenticate(self):
        self.client().post('/auth/register', data=self.user)
        req = self.client().post('/auth/login', data=self.user)
        return req


if __name__ == "__main__":
    unittest.main()
