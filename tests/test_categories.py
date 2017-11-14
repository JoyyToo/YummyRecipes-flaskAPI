import os, unittest, json
from app import app, db

from instance.config import app_config


class CategoriesTestCase(unittest.TestCase):
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = app.config.from_object(app_config[os.getenv('APP_SETTINGS')])
        self.client = app.test_client
        self.category = {'name': 'Dessert', 'description': 'after meals'}

        # binds the app to the current context
        with app.app_context():
            # create all tables
            db.create_all()

    def test_category_creation(self):
        """Test API can create a category (POST request)"""
        res = self.client().post('/category/', data=self.category)
        self.assertEqual(res.status_code, 201)
        self.assertIn('Dessert', str(res.data))

    def tearDown(self):
        """teardown all initialized variables."""
        with app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()


if __name__ == 'main':
    unittest.main()
