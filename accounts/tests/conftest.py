# pylint: disable=redefined-outer-name
"""Shared fixtures for accounts tests."""
import pytest
from django.contrib.auth import get_user_model
from accounts.models import Contact





@pytest.fixture
def user_data():
    """Return valid registration form data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "StrongPass123!",
        "password2": "StrongPass123!",
    }


@pytest.fixture
def contact_data():
    """Return valid contact data."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "linkedin": "https://linkedin.com/in/johndoe",
    }


@pytest.fixture
def phone_data():
    """Return valid phone data."""
    return {
        "phone_type": "mobile",
        "number": "+1234567890",
    }


@pytest.fixture
def test_user():
    """Create and return a test user."""


    user_model = get_user_model()
    return user_model.objects.create_user(
        username="existinguser",
        email="existing@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_contact(test_user, contact_data):
    """Create and return a test contact.""" 
    return Contact.objects.create(user=test_user, **contact_data)
