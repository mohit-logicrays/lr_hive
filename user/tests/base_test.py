from django.test import TestCase
from faker import Faker
from rest_framework.test import APIClient


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.fake = Faker()

    def field_required_error(self, data: dict) -> None:
        """
        Helper method to check if the response contains field required errors.
        """
        for error in data.values():
            if isinstance(error, list):
                assert "This field is required." in error
            else:
                assert "This field is required." == error

    def field_blank_error(self, data: dict) -> None:
        """
        Helper method to check if the response contains field blank errors.
        """
        for error in data.values():
            if isinstance(error, list):
                assert "This field may not be blank." in error
            else:
                assert "This field may not be blank." == error

    def is_pagination_response(self, data: dict) -> None:
        """
        Helper method to check if the response is a pagination response.
        """
        assert "count" in data
        assert "next" in data
        assert "previous" in data
        assert "results" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) >= 0
