from http import HTTPStatus

from django.urls import reverse
from user.constants import ValidationErrors
from user.tests.base_test import BaseTestCase
from user.tests.constants import UrlsNames
from user.tests.factories import UserFactory


class TestUserLogin(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(UrlsNames.LOGIN)
        self.user = UserFactory.create()
        self.user.set_password("password")
        self.user.save()

    def test_login_no_credentials(self):
        response = self.client.post(self.url, {})
        assert response.status_code == HTTPStatus.BAD_REQUEST
        self.field_required_error(data=response.json())

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            self.url, {"email": "invalid-email", "password": "invalid-password"}
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json().get("detail", "") == ValidationErrors.INVALID_CREDENTIALS

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            self.url, {"email": self.user.email, "password": "password"}
        )
        assert response.status_code == HTTPStatus.OK
        assert "access" in response.json()
        assert "refresh" in response.json()

    def test_token_refresh_invalid_refresh_token(self):
        invalid_refresh_token = "invalid-refresh-token"
        response = self.client.post(
            reverse(UrlsNames.REFRESH_TOKEN),
            {"refresh": invalid_refresh_token},
            format="json",
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED
        assert response.json().get("detail", "") == "Token is invalid"

    def test_token_refresh_valid_refresh_token(self):
        response = self.client.post(
            self.url, {"email": self.user.email, "password": "password"}
        )
        assert response.status_code == HTTPStatus.OK
        access_token = response.json().get("access")
        refresh_token = response.json().get("refresh")
        response = self.client.post(
            reverse(UrlsNames.REFRESH_TOKEN),
            {"refresh": refresh_token},
            format="json",
        )
        assert response.status_code == HTTPStatus.OK
        assert "access" in response.json()
        assert response.json().get("access") != access_token
        assert "refresh" in response.json()
        assert response.json().get("refresh") != refresh_token
