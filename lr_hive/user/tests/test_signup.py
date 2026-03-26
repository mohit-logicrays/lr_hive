from http import HTTPStatus

from django.urls import reverse
from user.models import User
from user.tests.base_test import BaseTestCase
from user.tests.constants import UrlsNames
from user.tests.factories import UserFactory


class TestSignUpView(BaseTestCase):
    def setUp(self):
        """
        Setup method to generate fake user data for testing sign up view.
        It also sets the url for sign up view.
        """
        super().setUp()
        self.url = reverse(UrlsNames.USERS_LIST)
        self.data = {
            "username": self.fake.user_name(),
            "first_name": self.fake.first_name(),
            "last_name": self.fake.last_name(),
            "email": self.fake.email(),
            "password": "Test@123456",
            "confirm_password": "Test@123456",
        }

    def test_user_signup_post_no_data(self):
        """
        Tests that the user sign up view returns a bad request status code
        and required field errors when no data is provided.
        """
        response = self.client.post(self.url, {})
        assert response.status_code == HTTPStatus.BAD_REQUEST
        self.field_required_error(data=response.json())

    def test_user_signup_empty_data(self):
        """
        Tests that the user sign up view returns a bad request status code
        and blank field errors when empty data is provided.
        """
        response = self.client.post(
            self.url,
            {
                "username": "",
                "email": "",
                "first_name": "",
                "password": "",
                "confirm_password": "",
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        self.field_blank_error(data=response.json())

    def test_user_signup_post_invalid_data(self):
        """
        Tests that the user sign up view returns a bad request status code
        and field validation errors when invalid data is provided.
        The test data contains an invalid email address, a password that is too
        short, and a confirm password field that does not match the password
        field.
        """
        data = {
            "email": "invalid-email",
            "password": "short",
            "confirm_password": "notmatching",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Enter a valid email address." in response.json()["email"]
        assert (
            "This password is too short. It must contain at least 8 characters."
            in response.json()["password"]
        )

    def test_user_signup_post_valid_data(self):
        """
        Tests that the user sign up view returns a created status code and
        the created user's data when valid data is provided.
        The test data contains a valid email address, a valid password,
        and a confirm password field that matches the password field.
        The test also checks that the user was created in the database
        and that the password was set correctly.
        """
        response = self.client.post(self.url, self.data)
        assert response.status_code == HTTPStatus.CREATED
        assert response.data["email"] == self.data["email"]
        assert response.data["first_name"] == self.data["first_name"]
        assert response.data["last_name"] == self.data["last_name"]
        assert response.data["username"] == self.data["username"]
        try:
            user = User.objects.get(username=self.data["username"])
            assert user.check_password(
                self.data["password"]
            ), "Password was not set correctly"
        except User.DoesNotExist as err:
            raise AssertionError("User was not created in the database") from err

    def test_user_signup_duplicate_data(self):
        """
        Tests that the user sign up view returns a bad request status code
        and field validation errors when a user with the same email or
        username already exists in the database.
        The test creates a new user and then tries to sign up with the same
        email and username. The test checks that the view returns a bad request
        status code and field validation errors for both the email and username
        fields.
        """
        user = UserFactory.create()
        self.data.update(
            {
                "username": user.username,
                "email": user.email,
            }
        )
        self.client.post(self.url, self.data)
        response = self.client.post(self.url, self.data)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "user with this Email already exists." in response.json()["email"]
        assert (
            "A user with that username already exists." in response.json()["username"]
        )
