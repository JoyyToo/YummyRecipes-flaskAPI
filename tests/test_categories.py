from flask import json
from tests.base_testcase import BaseTestCase


class CategoriesTestCase(BaseTestCase):
    """Test for categories"""

    def test_category_creation(self):
        """Test API can create a category (POST request)"""

        self.authenticate_and_create_category()

    def test_create_existing_category(self):
        """Tests creation of an already existing category"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().post('api/v1/category', headers=dict(Authorization="Bearer " + jwt_token),
                                    data=self.category)
        self.assertIn("Category already exists", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_create_category_with_empty_fields(self):
        """Test category creation with empty fields"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().post('api/v1/category', headers=dict(Authorization="Bearer " + jwt_token),
                                    data={'name': '', 'desc': ''})
        self.assertIn("Name or description cannot be empty", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_create_category_with_a_lot_of_characters(self):
        """Test category creation with a lot of characters"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().post('api/v1/category', headers=dict(Authorization="Bearer " + jwt_token),
                                    data={'name': 'Name or description cannot be emptyName or description cannot be '
                                                  'emptyName or description cannot be empty', 'desc': 'trial'})
        self.assertIn("Please make the length of the name less than 30 characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_if_user_can_retrieve_all_categories(self):
        """Test api can get all categories"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().get(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 200)

    def test_creation_with_invalid_characters(self):
        """Test api can get categories with invalid characters"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # create a category by making a POST request
        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': '@@%', 'desc': '$#'})
        self.assertIn("name contains invalid characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_if_user_can_retrieve_categories_by_id(self):
        """Test api can get categories by id"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().get(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 200)

    def test_if_get_non_existing_category(self):
        """Test if api can get non_existing category"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().get(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("No categories available at the moment", str(result.data))
        self.assertEqual(result.status_code, 401)

    def test_if_get_non_existing_category_by_id(self):
        """Test if api can get non_existing category by id"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().get(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("Category not found", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_category_editing(self):
        """Test category can be updated"""
        jwt_token = self.authenticate_create_and_get_category()

        # edit category
        result = self.client().put(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': 'new', 'desc': 'new'})
        self.assertEqual(result.status_code, 200)

    def test_category_editing_to_existing_name(self):
        """Test category can be updated"""
        jwt_token = self.authenticate_create_and_get_category()

        # create a category by making a POST request
        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': 'new', 'desc': 'new'})
        self.assertEqual(result.status_code, 201)

        # edit category
        result = self.client().put(
            'api/v1/category/2',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        self.assertEqual(result.status_code, 400)

    def test_edit_with_invalid_characters(self):
        """Test edit with invalid characters"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().put(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': 'new', 'desc': '$%&'})
        self.assertIn("desc contains invalid characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_edit_with_empty_fields(self):
        """Test edit with empty fields"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().put(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': '', 'desc': ''})
        self.assertEqual(result.status_code, 400)

    def test_edit_with_long_name(self):
        """Test edit with long name"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().put(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': 'est category edit non existing category category edit non existing category', 'desc': 'tr'})
        self.assertIn("Please make the length of the name less than 30 characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_edit_non_existing_category(self):
        """Test category edit non existing category"""

        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # edit non existing category
        result = self.client().put(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            )
        self.assertEqual(result.status_code, 404)

    def test_category_deletion(self):
        """Test category can be deleted"""
        jwt_token = self.authenticate_create_and_get_category()

        # delete the category
        result = self.client().delete(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertEqual(result.status_code, 200)

    def test_delete_non_existing_category(self):
        """Test deletion of non existing category"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # delete the category
        result = self.client().delete(
            'api/v1/category/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertEqual(result.status_code, 404)

    def test_search_existing_category(self):
        """Test api can search existing category"""
        jwt_token = self.authenticate_and_create_category()

        result = self.client().get(
            'api/v1/category?q=name',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 200)

    def test_search_non_existing_category(self):
        """Test searching non existing category"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?q=des',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 404)

    def test_correct_page_number(self):
        """Test if api can take correct page number"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 200)

    def test_negative_page_number(self):
        """Test if api can take a negative page number"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?limit=1&page=-7',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 400)
        self.assertIn('Page number must be a positive integer!! ', str(result.data))

    def test_non_existing_page_number(self):
        """Test if api can take a non existing  page number"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?limit=1&page=7',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 404)

    def test_correct_limit(self):
        """Test if api can take correct limit"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 200)

    def test_negative_limit(self):
        """Test if api can take negative limit"""
        jwt_token = self.authenticate_create_and_get_category()

        result = self.client().get(
            'api/v1/category?limit=-1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 400)
        self.assertIn('Limit number must be a positive integer!!', str(result.data))
