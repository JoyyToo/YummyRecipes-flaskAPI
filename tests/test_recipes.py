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

    def test_search_existing_recipe(self):
        """Test api can search existing recipe"""
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
            'api/v1/category/1/recipes?q=mea',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn('meat pie', str(req.data))

    def test_search_non_existing_recipe(self):
        """Test api can searching non existing recipe"""
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
            'api/v1/category/1/recipes?q=des',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 401)

    def test_correct_page_no(self):
        """Test api can take correct page no"""
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
            'api/v1/category/1/recipes?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 200)

    def test_negative_page_no(self):
        """Test api can take negative page no"""
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
            'api/v1/category/1/recipes?limit=1&page=-1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 400)

    def test_correct_limit(self):
        """Test api can take correct limit"""
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
            'api/v1/category/1/recipes?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 200)

    def test_negative_limit(self):
        """Test api can take a negative limit"""
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
            'api/v1/category/1/recipes?limit=-1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(res.status_code, 400)










