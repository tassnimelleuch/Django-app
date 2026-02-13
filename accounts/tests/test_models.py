"""
Tests for Contact and PhoneNumber models in the accounts app.
"""

import time
import pytest
from django.contrib.auth import get_user_model

# pylint: disable=no-member
from accounts.models import Contact, PhoneNumber

User = get_user_model()


# ===== CONTACT MODEL TESTS =====

@pytest.mark.django_db
def test_contact_creation_minimal():
    """Create a contact with minimal required fields."""
    user = User.objects.create_user(username="testuser", password="testpass")

    contact = Contact.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
    )

    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.last_name == "Doe"
    assert contact.user == user
    assert contact.email is None
    assert contact.linkedin is None


@pytest.mark.django_db
def test_contact_creation_with_all_fields():
    """Create a contact with all optional fields."""
    user = User.objects.create_user(username="testuser", password="testpass")

    contact = Contact.objects.create(
        user=user,
        first_name="Jane",
        last_name="Smith",
        email="jane@example.com",
        linkedin="https://linkedin.com/in/janesmith",
    )

    assert contact.email == "jane@example.com"
    assert contact.linkedin == "https://linkedin.com/in/janesmith"


@pytest.mark.django_db
def test_contact_updated_at_changes_on_save():
    """updated_at should change when the contact is modified."""
    user = User.objects.create_user(username="testuser", password="testpass")

    contact = Contact.objects.create(
        user=user,
        first_name="Original",
        last_name="Name",
    )

    original_updated_at = contact.updated_at
    time.sleep(0.01)

    contact.first_name = "Updated"
    contact.save()

    assert contact.updated_at > original_updated_at


@pytest.mark.django_db
def test_contact_cascade_delete():
    """Deleting a user should delete related contacts."""
    user = User.objects.create_user(username="testuser", password="testpass")

    contact = Contact.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
    )
    contact_id = contact.id

    user.delete()

    with pytest.raises(Contact.DoesNotExist):
        Contact.objects.get(id=contact_id)


# ===== PHONE NUMBER MODEL TESTS =====

@pytest.mark.django_db
def test_phone_number_creation():
    """Create a phone number for a contact."""
    user = User.objects.create_user(username="testuser", password="testpass")
    contact = Contact.objects.create(user=user, first_name="John", last_name="Doe")

    phone = PhoneNumber.objects.create(
        contact=contact,
        phone_type="mobile",
        number="+1234567890",
    )

    assert phone.id is not None
    assert phone.phone_type == "mobile"
    assert phone.number == "+1234567890"
    assert phone.contact == contact


@pytest.mark.django_db
def test_phone_number_default_type():
    """Phone type should default to 'mobile'."""
    user = User.objects.create_user(username="testuser", password="testpass")
    contact = Contact.objects.create(user=user, first_name="John", last_name="Doe")

    phone = PhoneNumber.objects.create(
        contact=contact,
        number="+1234567890",
    )

    assert phone.phone_type == "mobile"


@pytest.mark.django_db
def test_phone_number_valid_choices():
    """All valid phone type choices should work."""
    user = User.objects.create_user(username="testuser", password="testpass")
    contact = Contact.objects.create(user=user, first_name="John", last_name="Doe")

    for phone_type in ("mobile", "home", "work", "other"):
        phone = PhoneNumber.objects.create(
            contact=contact,
            phone_type=phone_type,
            number="+1234567890",
        )
        assert phone.phone_type == phone_type


@pytest.mark.django_db
def test_phone_number_cascade_delete():
    """Deleting a contact should delete related phone numbers."""
    user = User.objects.create_user(username="testuser", password="testpass")
    contact = Contact.objects.create(user=user, first_name="John", last_name="Doe")

    phone = PhoneNumber.objects.create(
        contact=contact,
        number="+1234567890",
    )
    phone_id = phone.id

    contact.delete()

    with pytest.raises(PhoneNumber.DoesNotExist):
        PhoneNumber.objects.get(id=phone_id)


@pytest.mark.django_db
def test_multiple_phones_per_contact():
    """A contact can have multiple phone numbers."""
    user = User.objects.create_user(username="testuser", password="testpass")
    contact = Contact.objects.create(user=user, first_name="John", last_name="Doe")

    phones_data = (
        {"number": "1111111111", "phone_type": "mobile"},
        {"number": "2222222222", "phone_type": "home"},
        {"number": "3333333333", "phone_type": "work"},
    )

    for data in phones_data:
        PhoneNumber.objects.create(contact=contact, **data)

    assert contact.phone_numbers.count() == 3
    assert set(contact.phone_numbers.values_list("number", flat=True)) == {
        "1111111111",
        "2222222222",
        "3333333333",
    }
