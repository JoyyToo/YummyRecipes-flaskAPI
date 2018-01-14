import unittest
import json
import jwt
import time
from datetime import datetime, timedelta

from app import app
from tests.base_testcase import BaseTestCase


class TestUserAuth(BaseTestCase):
    """Tests for correct user authentication."""

    # ENDPOINT: POST '/auth/register'
    def test_registration_for_user(self):
        """Tests for successful user registration."""
        result = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 201)
        self.assertIn(b"You registered successfully. Please log in.", result.data)

    def test_registration_for_existing_user(self):
        """Tests for registration of existing user."""
        self.client().post('/api/v1/auth/register', data=self.user)
        result = self.client().post('/api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 409)
        self.assertIn(b"User already exists. Please login", result.data)

    def test_registration_for_empty_fields(self):
        """Tests for registration with empty fields"""
        self.user = {'email': self.fake.email(), 'username': '', 'password': ''}

        result = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 400)
        self.assertIn(b"Please fill all fields", result.data)

    def test_registration_with_invalid_characters(self):
        """Tests for registration with invalid characters"""
        self.user = {'email': self.fake.email(), 'username': '@@@@', 'password': 'password'}

        result = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 400)
        self.assertIn(b"Username contains invalid characters", result.data)

    def test_registration_with_a_lot_of_characters(self):
        """Tests for registration with alot of characters"""
        self.user = {'email': self.fake.email(), 'username': 'Unauthorized, Please login or registerUnauthorized, '
                                                             'Please login or registerUnauthorized, Please login '
                                                             'or register', 'password': 'password'}

        result = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 400)
        self.assertIn(b"Please make the length of the email or username less than 40 characters", result.data)

    def test_invalid_email_address(self):
        """Tests for registration with invalid email"""
        self.user = {'email': '', 'username': self.fake.name(), 'password': 123456}

        result = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 400)
        self.assertIn(b"Please enter a valid email address", result.data)

    def test_registration_for_password_less_than_6(self):
        """Tests for registration with password less than 6 characters"""
        self.user = {'email': self.fake.email(), 'username': self.fake.name(), 'password': 1234}

        result = self.client().post('api/v1/auth/register', data=self.user)

        self.assertEqual(result.status_code, 400)
        self.assertIn(b"Password must be more than 6 characters.", result.data)

    # ENDPOINT: POST '/auth/login'
    def test_for_user_login(self):
        """Tests for correct user login."""

        result = self.authenticate()

        self.assertIn(b"You logged in successfully.", result.data)

    def test_invalid_login(self):
        """Tests for invalid user login."""

        result = self.client().post('api/v1/auth/register', data=self.user)
        self.assertEqual(result.status_code, 201)

        result = self.client().post('api/v1/auth/login', data=self.wrong_user)
        self.assertIn(b"Invalid email or password, Please try again", result.data)

    # ENDPOINT: POST '/auth/reset-logout'
    def test_for_user_logout(self):
        """Tests for correct user logout."""
        self.client().post('api/v1/auth/register', data=self.user)
        result = self.client().post('api/v1/auth/login', data=self.user)

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post(
            'api/v1/auth/logout',
            headers=dict(Authorization="Bearer " + jwt_token),
            data=self.user)
        self.assertIn(b"You logged out successfully.", result.data)
        self.assertEqual(result.status_code, 200)

    # ENDPOINT: POST '/auth/reset-password'
    def test_reset_with_non_existing_email(self):
        """Tests reset password with non existing email"""

        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': 'test@mail.com', 'new password': 'newnew'})
        self.assertIn(b"User email does not exist.", result.data)
        self.assertEqual(result.status_code, 404)

    def test_reset_with_invalid_email(self):
        """Tests reset password with email containing invalid characters"""

        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': 'test@mail.com.com', 'new password': 'newnew'})
        self.assertIn(b"Email Invalid. Do not include special characters.", result.data)
        self.assertEqual(result.status_code, 400)

    def _test_reset_with_password_less_than_6_characters(self):
        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': self.user['email'], 'new password': 'new'})
        self.assertIn(b"Password must be 6 or more characters.", result.data)
        self.assertEqual(result.status_code, 400)

    # tokens
    def test_for_unauthorized_login(self):
        """Tests for unauthorized login"""
        self.authenticate()

        result = self.client().post(
            'api/v1/category',
            data=self.category)
        self.assertIn(b"Unauthorized, Please login or register", result.data)
        self.assertEqual(result.status_code, 403)

    def test_for_missing_bearer(self):
        """Test token with missing bearer prefix"""
        self.authenticate()

        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="hiuuivuv"),
            data=self.category)
        self.assertIn(b"Please Use Bearer before adding token [Bearer <token>]", result.data)
        self.assertEqual(result.status_code, 403)

    def test_for_invalid_token(self):
        """Test for invalid token"""
        self.authenticate()

        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization="Bearer hiuuivuv"),
            data=self.category)
        self.assertIn(b"Invalid token. Please register or login", result.data)
        self.assertEqual(result.status_code, 403)

    def test_for_expired_token(self):
        """Test for expired token"""
        self.authenticate()
        payload = {
            'exp': datetime.utcnow() + timedelta(seconds=1),
            'iat': datetime.utcnow(),
            'sub': 1,
        }

        jwt_token = jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )
        time.sleep(2)

        result = self.client().post(
            'api/v1/category',
            headers=dict(Authorization=b"Bearer " + jwt_token),
            data=self.category)
        self.assertIn(b"Expired token. Please login to get a new token", result.data)
        self.assertEqual(result.status_code, 403)


if __name__ == 'main':
    unittest.main()
