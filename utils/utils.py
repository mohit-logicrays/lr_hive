# Devloka Utilities Module
# This module contains utility functions for the Devloka project.


def normalize_email(email: str) -> str:
    """
    Normalize the email address by converting it to lowercase.

    Args:
        email (str): The email address to normalize.

    Returns:
        str: The normalized email address in lowercase.
    """
    return email.lower().strip()
