# User List Tests
from http import HTTPStatus

from django.urls import reverse

from user.models import User
from user.tests.base_test import BaseTestCase
from user.tests.constants import UrlsNames
from user.tests.factories import UserFactory


class TestUsersListView(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(UrlsNames.USERS_LIST)
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

    def test_users_list_get(self):
        """
        Tests that the user list view returns a success status code and
        a list of users when a GET request is made.
        """
        response = self.client.get(self.url)
        assert response.status_code == HTTPStatus.OK
        assert isinstance(response.data, dict)
        self.is_pagination_response(data=response.data)
        results = response.data["results"]
        for user in results:
            assert User.objects.filter(**user).exists()
