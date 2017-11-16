from flask import json
import os
from app import app, db
from instance.config import app_config
from tests.base_testcase import BaseTestCase


class CategoriesTestCase(BaseTestCase):
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
        pass

