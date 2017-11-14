import os, unittest, json

from tests.base_testcase import BaseTestCase


class TestUserAuth(BaseTestCase):
    """Tests for correct user authentiaction."""

    # ENDPOINT: POST '/auth/register'
    def test_registration_for_existing_user(self):
        """Tests for user registration with existing email."""
        req = self.client().post('/auth/register', data=self.user)
        self.assertEqual(req.status_code, 202)

        same_user = self.user
        req = self.client().post('api/v1/auth/register', data=same_user)

        self.assertNotEqual(req.status_code, 201)

    def test_registration(self):
        """Test user registration works correcty."""
        res = self.client().post('/auth/register', data=self.user)
        self.assertEqual(res.status_code, 201)
        result = json.loads(res.data.decode())
        self.assertEqual(result['message'], "You registered successfully. Please log in.")


if __name__ == 'main':
    unittest.main()
