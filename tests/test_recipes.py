from flask import json
from tests.base_testcase import BaseTestCase


class RecipesTestCase(BaseTestCase):
    """Test recipes"""

    def test_recipe_creation(self):
        """Test recipe can be created"""

        self.authenticate()
        self.create_category()
        result = self.create_recipe()

        self.assertEqual(result.status_code, 201)
        self.assertIn('Recipe added successfully', str(result.data))

    def test_recipe_creation_for_non_existing_category(self):
        """Test recipe creation with non existing category  """
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post('api/v1/category/1/recipes', headers=dict(Authorization="Bearer " + jwt_token),
                                    data=self.recipe)
        self.assertEqual(result.status_code, 404)

    def test_recipe_creation_with_empty_fields(self):
        """Test recipe creation with empty fields"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().post('api/v1/category/1/recipes', headers=dict(Authorization="Bearer " + jwt_token),
                                    data={'name': '', 'time': '', 'ingredients': '', 'procedure': ''})
        self.assertIn("Name or time or ingredients or procedure cannot be empty", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_recipe_creation_with_long_characters(self):
        """Test recipe creation with long characters"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().post('api/v1/category/1/recipes', headers=dict(Authorization="Bearer " + jwt_token),
                                    data={'name': 'Name or time or ingredients or procedure cannot be empty',
                                          'time': '1 hour', 'ingredients': 'flour', 'procedure': 'bake'})
        self.assertIn("Please make the name or time shorter than 30 characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_create_existing_recipe(self):
        """Test create existing recipe"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().post('api/v1/category/1/recipes', headers=dict(Authorization="Bearer " + jwt_token),
                                    data=self.recipe)

        self.assertEqual(result.status_code, 401)
        self.assertIn('Recipe already exists', str(result.data))

    def test_recipe_creation_with_invalid_characters(self):
        """Test recipe can be created with invalid characters"""

        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().post('api/v1/category/1/recipes', headers=dict(Authorization="Bearer " + jwt_token),
                                    data={'name': '$$$', 'time': 'whedio', 'ingredients': 'wkehri',
                                          'procedure': 'weiuyiu'})

        self.assertEqual(result.status_code, 400)
        self.assertIn('name contains invalid characters', str(result.data))

    def test_if_user_can_retrieve_all_recipes(self):
        """Test api can get all recipes"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 200)

    def test_if_user_can_retrieve_all_recipes_when_category_is_non_existing(self):
        """Test api can get all recipes with non existing category"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/2/recipes',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 404)

    def test_if_user_can_retrieve_recipes_by_id(self):
        """Test api can get recipes by id"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 200)

    def test_if_get_non_existing_recipe(self):
        """Test if api can get non_existing recipe"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # get with non existing category by id
        result = self.client().get(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("Category does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_get_with_with_non_existing_category(self):
        """Test get with non existing category"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().get(
            'api/v1/category/1/recipes',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("Category does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_get_with_category_and_missing_recipe_by_id(self):
        """Test get with category and non existing recipe by id"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().get(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("Recipe not available at the moment", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_get_all_non_existing_recipes_with_category(self):
        """Test get all non existing recipes with category"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        json.loads(result.data.decode())

        result = self.client().get(
            'api/v1/category/1/recipes',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertIn("Recipe not available at the moment", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_if_get_recipe_from_non_existing_category(self):
        """Test if api can get recipe from non_existing category"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # get with non existing category
        result = self.client().get(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            )
        self.assertIn("Category does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_recipe_editing(self):
        """Test recipe can be edited"""

        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        # edit recipe
        result = self.client().put(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': 'new', 'time': 'new', 'ingredients': 'new', 'procedure': 'new'})
        self.assertEqual(result.status_code, 200)

    def test_recipe_editing_to_an_existing_name(self):
        """Test recipe editing to an existing name"""

        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        # create a category by making a POST request
        self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.category)
        self.client().post('api/v1/category/1/recipes',
                           headers=dict(Authorization="Bearer " + jwt_token),
                           data={'name': 'new', 'time': 'new', 'ingredients': 'new', 'procedure': 'new'})
        # edit recipe
        result = self.client().put(
            'api/v1/category/1/recipes/2',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.recipe)
        self.assertEqual(result.status_code, 400)

    def test_edit_with_invalid_characters(self):
        """edit recipe with invalid characters"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        result = self.client().put(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'name': '&^%', 'time': 'new', 'ingredients': 'new', 'procedure': 'new'})
        self.assertIn("name contains invalid characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_recipe_editing_with_long_characters(self):
        """Test recipe editing with long characters"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        result = self.client().put('api/v1/category/1/recipes/1', headers=dict(Authorization="Bearer " + jwt_token),
                                   data={'name': 'Name or time or ingredients or procedure cannot be empty',
                                         'time': '1 hour', 'ingredients': 'flour', 'procedure': 'bake'})
        self.assertIn("Please make the length of the name or time shorter than 30 characters", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_edit_with_empty_fields(self):
        """check edit with  fields are empty"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        result = self.client().put('api/v1/category/1/recipes/1', headers=dict(Authorization="Bearer " + jwt_token),
                                   data={'name': '', 'time': '', 'ingredients': '', 'procedure': ''})
        self.assertIn("Name or time or ingredients or procedure cannot be empty", str(result.data))
        self.assertEqual(result.status_code, 400)

    def test_edit_non_existing_recipe(self):
        """Test category edit non existing recipe"""

        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # edit non existing category
        result = self.client().put(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token),
            )
        self.assertIn("Category does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_edit_recipe_with_category_but_no_recipe(self):
        """edit the recipe with category but no recipe"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().put(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertIn("Recipe not found", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_recipe_deletion(self):
        """Test recipe can be deleted"""

        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        json.loads(result.data.decode())

        # delete the category
        result = self.client().delete(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertEqual(result.status_code, 200)

    def test_delete_non_existing_recipe(self):
        """Test deletion of non existing recipe"""
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        # delete the recipe without category
        result = self.client().delete(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertIn("Category does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_delete_with_category_but_no_recipe(self):
        """Test delete the recipe with category but no recipe"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()

        result = self.client().delete(
            'api/v1/category/1/recipes/1',
            headers=dict(Authorization="Bearer " + jwt_token), )
        self.assertIn("Recipe does not exist", str(result.data))
        self.assertEqual(result.status_code, 404)

    def test_search_existing_recipe(self):
        """Test api can search existing recipe"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?q=mea',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 200)

    def test_search_non_existing_recipe(self):
        """Test api can searching non existing recipe"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?q=des',
            headers=dict(Authorization="Bearer " + jwt_token),
        )
        self.assertEqual(result.status_code, 404)

    def test_correct_page_number(self):
        """Test api can take correct page number"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 200)

    def test_negative_page_number(self):
        """Test if api can take negative page number"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?limit=1&page=-1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 400)
        self.assertIn('Page number must be a positive integer!! ', str(result.data))

    def test_non_existent__page_number(self):
        """Test if api can take non existent page number"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?limit=1&page=7',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 404)

    def test_correct_limit(self):
        """Test api can take correct limit"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?limit=1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 200)

    def test_negative_limit(self):
        """Test api can take a negative limit"""
        result = self.authenticate()
        jwt_token = json.loads(result.data.decode())['jwt_token']
        self.create_category()
        self.create_recipe()

        result = self.client().get(
            'api/v1/category/1/recipes?limit=-1&page=1',
            headers=dict(Authorization="Bearer " + jwt_token), data=self.category
        )
        self.assertEqual(result.status_code, 400)
        self.assertIn('Limit number must be a positive integer!!', str(result.data))
