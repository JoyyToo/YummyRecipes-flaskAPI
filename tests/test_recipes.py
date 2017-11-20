from flask import json
from tests.base_testcase import BaseTestCase


class RecipesTestCase(BaseTestCase):
    """Test recipes"""

    def test_category_creation(self):
        """Test recipe can be created"""

        req = self.authenticate()

        jwt_token = json.loads(req.data.decode())['jwt_token']

        # create a category by making a POST request
        self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        req = self.client().post('api/v1/category/1/recipes',
                                 headers=dict(Authorization="Bearer " + jwt_token),
                                 data=self.recipe)

        self.assertEqual(req.status_code, 201)
        self.assertIn('Recipe added successfully', str(req.data))

    def test_if_user_can_retrieve_all_recipes(self):
        """Test api can get all recipes"""
        req = self.authenticate()

        jwt_token = json.loads(req.data.decode())['jwt_token']

        # create a category by making a POST request
        self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        req = self.client().post('api/v1/category/1/recipes',
                                 headers=dict(Authorization="Bearer " + jwt_token),
                                 data=self.recipe)
        self.assertEqual(req.status_code, 201)

        res = self.client().get(
            'api/v1/category/1/recipes',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(res.status_code, 200)

    def test_category_deletion(self):
        """Test category can be deleted"""

        req = self.authenticate()

        jwt_token = json.loads(req.data.decode())['jwt_token']

        # create a category by making a POST request
        self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        req = self.client().post('api/v1/category/1/recipes',
                                 headers=dict(Authorization="Bearer " + jwt_token),
                                 data=self.recipe)
        self.assertEqual(req.status_code, 201)

        # get the category in json
        req = json.loads(req.data.decode())

        # delete the category
        req = self.client().delete(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertEqual(req.status_code, 200)







