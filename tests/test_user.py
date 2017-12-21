import unittest
import json

from tests.base_testcase import BaseTestCase


class TestUserAuth(BaseTestCase):
    """Tests for correct user authentication."""

    # ENDPOINT: POST '/auth/register'
    def test_registration_for_user(self):
        """Tests for successful user registration."""
        req = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 201)
        self.assertIn(b"You registered successfully. Please log in.", req.data)

    def test_registration_for_existing_user(self):
        """Tests for registration of existing user."""
        self.client().post('/api/v1/auth/register', data=self.user)
        req = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 409)
        self.assertIn(b"User already exists. Please login", req.data)

    def test_registration_for_empty_fields(self):
        """Tests for registration with empty fields"""
        self.user = {'email': self.fake.email(), 'username': '', 'password': ''}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn(b"Please fill all fields", req.data)

    def test_registration_with_invalid_characters(self):
        """Tests for registration with invalid characters"""
        self.user = {'email': self.fake.email(), 'username': '@@@@', 'password': 'password'}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn(b"Username contains invalid characters", req.data)

    def test_invalid_email_address(self):
        """Tests for registration with invalid email"""
        self.user = {'email': '', 'username': self.fake.name(), 'password': 123456}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn(b"Please enter a valid email address", req.data)

    def test_registration_for_password_less_than_6(self):
        """Tests for registration with password less than 6 characters"""
        self.user = {'email': self.fake.email(), 'username': self.fake.name(), 'password': 1234}

        req = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(req.status_code, 400)
        self.assertIn(b"Password must be more than 6 characters.", req.data)

    # ENDPOINT: POST '/auth/login'
    def test_for_user_login(self):
        """Tests for correct user login."""

        req = self.client().post('api/v1/auth/register', data=self.user)
        self.assertEqual(req.status_code, 201)

        req = self.client().post('api/v1/auth/login', data=self.user)

        self.assertIn(b"You logged in successfully.", req.data)

        req = self.client().post('api/v1/auth/login', data=self.wrong_user)
        self.assertIn(b"Invalid email or password, Please try again", req.data)

    # ENDPOINT: POST '/auth/reset-logout'
    def test_for_user_logout(self):
        """Tests for correct user logout."""
        self.client().post('api/v1/auth/register', data=self.user)
        req = self.client().post('api/v1/auth/login', data=self.user)

        jwt_token = json.loads(req.data.decode())['jwt_token']

        req = self.client().get(
            'api/v1/auth/logout',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.user)
        self.assertIn(b"You logged out successfully.", req.data)
        self.assertEqual(req.status_code, 200)

    # ENDPOINT: POST '/auth/reset-password'
    def test_for_user_reset_password(self):
        """Tests for correct reset password"""

        self.client().post('api/v1/auth/register', data=self.user)
        req = self.client().post('api/v1/auth/login', data=self.user)

        jwt_token = json.loads(req.data.decode())['jwt_token']

        req = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': self.user['email'], 'new password': 'newnew'})
        self.assertIn(b"Password reset. You can now login with new password.", req.data)
        self.assertEqual(req.status_code, 200)

        req = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': 'test@mail.com', 'new password': 'newnew'})
        self.assertIn(b"User email does not exist.", req.data)
        self.assertEqual(req.status_code, 404)

        req = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': 'test@mail.com.com', 'new password': 'newnew'})
        self.assertIn(b"Email Invalid. Do not include special characters.", req.data)
        self.assertEqual(req.status_code, 400)

        req = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': self.user['email'], 'new password': 'new'})
        self.assertIn(b"Password must be 6 or more characters.", req.data)
        self.assertEqual(req.status_code, 400)

    # tokens
    def test_for_unauthorized_login(self):
        """Tests for unauthorized login"""
        self.client().post('api/v1/auth/register', data=self.user)
        req = self.client().post('api/v1/auth/login', data=self.user)

        req = self.client().post(
            'api/v1/auth/reset-password',
            data=self.user)
        self.assertIn(b"Unauthorized, Please login or register", req.data)
        self.assertEqual(req.status_code, 403)

        # index error
        self.client().post('api/v1/auth/register', data=self.user)
        req = self.client().post('api/v1/auth/login', data=self.user)

        req = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="hiuuivuv"),
            data=self.user)
        self.assertIn(b"Please Use Bearer before adding token [Bearer <token>]", req.data)
        self.assertEqual(req.status_code, 403)


if __name__ == 'main':
    unittest.main()
