import os, unittest, json

from tests.base_testcase import BaseTestCase


class TestUserAuth(BaseTestCase):
    """Tests for correct user authentication."""

    # ENDPOINT: POST '/auth/register'
    def test_registration_for_user(self):
        """Tests for successful user registration."""
        req = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 201)
        self.assertIn("You registered successfully. Please log in.", req.data)

    def test_registration_for_existing_user(self):
        """Tests for registration of existing user."""
        self.client().post('/api/v1/auth/register', data=self.user)
        req = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 409)
        self.assertIn("User already exists. Please login", req.data)

    def test_registration_for_empty_fields(self):
        """Tests for registration with empty fields"""
        self.user = {'email': '', 'username': '', 'password': ''}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn("Please fill all fields", req.data)

    def test_registration_for_password_less_than_6(self):
        """Tests for registration with password less than 6 characters"""
        self.user = {'email': self.fake.email(), 'username': self.fake.name(), 'password': 1234}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn("Password must be more than 6 characters.", req.data)

    # ENDPOINT: POST '/auth/login'
    def test_for_user_login(self):
        """Tests for correct user login."""

        req = self.client().post('api/v1/auth/register', data=self.user)
        self.assertEqual(req.status_code, 201)

        req = self.client().post('api/v1/auth/login', data=self.user)

        self.assertIn("You logged in successfully.", req.data)

        req = self.client().post('api/v1/auth/login', data=self.wrong_user)
        self.assertIn("Invalid email or password, Please try again", req.data)


if __name__ == 'main':
    unittest.main()
