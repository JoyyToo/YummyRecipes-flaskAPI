import unittest
import json

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
    def test_for_user_reset_password(self):
        """Tests for correct reset password"""

        result = self.authenticate()

        jwt_token = json.loads(result.data.decode())['jwt_token']

        result = self.client().post(
            'api/v1/auth/reset-password',
            headers=dict(Authorization="Bearer " + jwt_token),
            data={'email': self.user['email'], 'new password': 'newnew'})
        result_data = json.loads(result.data.decode())
        self.assertIn(result_data['message'], 'Email sent to : {} <br/>'.format(self.user['email']))
        self.assertEqual(result.status_code, 200)

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

    # new password
    def _test_correct_new_password(self):
        result = self.client().post(
            'api/v1/auth/new-password/iqehiquehy3843264728qyer7348584356',
            data={'new password': 'newnew'})
        result_data = json.loads(result.data.decode())
        self.assertIn(result_data['message'], "Password for {} has been reset. You can now login".format(
            self.user['email'], 'new password'),)
        self.assertEqual(result.status_code, 400)

    def _test_new_password_less_than_6_characters(self):
        result = self.client().post(
            'api/v1/auth/new-password/<token>',
            data={'new password': 'new'})
        self.assertIn("Password must be more than 6 characters.".format(
            self.user['email'], 'new password'), result.data)
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


if __name__ == 'main':
    unittest.main()
