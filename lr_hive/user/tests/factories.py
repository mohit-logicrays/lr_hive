from factory.django import DjangoModelFactory
from faker import Faker
from user.models import User

fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = fake.user_name()
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email()
