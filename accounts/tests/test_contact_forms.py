"""Tests for contact and phone number forms in the accounts app."""
import pytest
from accounts.contact_forms import ContactForm, PhoneNumberForm


@pytest.mark.django_db
def test_contact_form_requires_name_fields(contact_data):
    """Contact must have first and last name."""
    data = contact_data.copy()
    del data['first_name']
    del data['last_name']
    form = ContactForm(data=data)
    assert not form.is_valid()
    assert 'first_name' in form.errors
    assert 'last_name' in form.errors


@pytest.mark.django_db
def test_contact_form_invalid_email_rejected(contact_data):
    """Invalid email format should be rejected."""
    data = contact_data.copy()
    data['email'] = 'not-an-email'
    form = ContactForm(data=data)
    assert not form.is_valid()
    assert 'email' in form.errors


@pytest.mark.django_db
def test_contact_form_invalid_url_rejected(contact_data):
    """Invalid LinkedIn URL should be rejected."""
    data = contact_data.copy()
    data['linkedin'] = 'not-a-url'
    form = ContactForm(data=data)
    assert not form.is_valid()
    assert 'linkedin' in form.errors


@pytest.mark.django_db
def test_contact_form_saves_correctly(contact_data, test_user):
    """Form should save Contact instance correctly."""
    form = ContactForm(data=contact_data)
    assert form.is_valid()
    contact = form.save(commit=False)
    contact.user = test_user
    contact.save()
    assert contact.id is not None
    assert contact.first_name == 'John'
    assert contact.last_name == 'Doe'
    assert contact.email == 'john@example.com'


@pytest.mark.django_db
def test_phone_form_requires_number(phone_data):
    """Phone number is required."""
    data = phone_data.copy()
    data['number'] = ''
    form = PhoneNumberForm(data=data)
    assert not form.is_valid()
    assert 'number' in form.errors


@pytest.mark.django_db
def test_phone_number_form_saves_correctly(phone_data, contact_data, test_user):
    """Form should save PhoneNumber linked to Contact."""
    contact_form = ContactForm(data=contact_data)
    assert contact_form.is_valid()
    contact = contact_form.save(commit=False)
    contact.user = test_user
    contact.save()
    phone_form = PhoneNumberForm(data=phone_data)
    assert phone_form.is_valid()
    phone = phone_form.save(commit=False)
    phone.contact = contact
    phone.save()
    assert phone.id is not None
    assert phone.number == '+1234567890'
    assert phone.phone_type == 'mobile'
    assert phone.contact == contact
