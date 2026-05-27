"""Tests for registration form in the accounts app."""
import pytest

from accounts.forms import RegisterForm

@pytest.mark.django_db
def test_register_form_duplicate_username_rejected(
    user_data, test_user
):
    """Duplicate username should be rejected."""
    data = user_data.copy()
    data["username"] = test_user.username
    form = RegisterForm(data=data)
    assert not form.is_valid()
    assert "username" in form.errors


@pytest.mark.django_db
def test_register_form_duplicate_email_rejected(
    user_data, test_user
):
    """Duplicate email should be rejected."""
    data = user_data.copy()
    data["email"] = test_user.email
    form = RegisterForm(data=data)
    assert not form.is_valid()
    assert "email" in form.errors
