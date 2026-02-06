"""Tests for views in the accounts app."""


# pylint: disable=no-member


import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from accounts.models import Contact, PhoneNumber

User = get_user_model()


# ===== REGISTRATION VIEW TESTS =====

def test_register_view_get(client):
    """Test GET request to register page."""
    response = client.get(reverse('register'))
    assert response.status_code == 200
    assert 'form' in response.context
    assert 'accounts/register.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_register_view_post_valid(client, user_data):
    """Test POST with valid registration data."""
    # Use user_data from conftest.py
    data = user_data.copy()
    data['username'] = 'newuser'  # Change to avoid duplicate
    data['email'] = 'newuser@example.com'  # Change to avoid duplicate
    response = client.post(reverse('register'), data)
    # Should redirect to login
    assert response.status_code == 302
    assert response.url == reverse('login')
    # User should be created
    assert User.objects.filter(username='newuser').exists()
    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert 'Account created' in str(messages[0])


@pytest.mark.django_db
def test_register_view_post_invalid(client):
    """Test POST with invalid registration data."""
    data = {
        'username': '',  # Missing username
        'email': 'invalid-email',
        'password1': '123',
        'password2': '456'  # Mismatch
    }

    response = client.post(reverse('register'), data)
    # Should return form with errors
    assert response.status_code == 200
    assert 'form' in response.context
    assert response.context['form'].errors


# ===== LOGIN/LOGOUT TESTS =====

@pytest.mark.django_db
def test_logout_view(client, test_user):
    """Test logout view redirects to login."""
    client.force_login(test_user)
    response = client.get(reverse('logout'))
    assert response.status_code == 302
    assert response.url == reverse('login')
    # User should be logged out
    response = client.get(reverse('dashboard'))
    # Should redirect to login since logged out
    assert response.status_code == 302


# ===== DASHBOARD VIEW TESTS =====

def test_dashboard_view_requires_login(client):
    """Test dashboard redirects if not logged in."""
    response = client.get(reverse('dashboard'))
    # Should redirect to login page
    assert response.status_code == 302
    assert '/login' in response.url


@pytest.mark.django_db
def test_dashboard_view_authenticated(client, test_user):
    """Test dashboard works when logged in."""
    client.force_login(test_user)
    response = client.get(reverse('dashboard'))
    assert response.status_code == 200
    assert 'accounts/dashboard.html' in [t.name for t in response.templates]
    assert 'user' in response.context


# ===== CONTACT LIST VIEW TESTS =====

def test_contact_list_requires_login(client):
    """Test contact list requires authentication."""
    response = client.get(reverse('contact_list'))
    assert response.status_code == 302  # Redirect to login


@pytest.mark.django_db
def test_contact_list_authenticated(client, test_user):
    """Test contact list shows user's contacts."""
    client.force_login(test_user)
    # Create contacts for test_user
    contact1 = Contact.objects.create(user=test_user, first_name='John',
                                      last_name='Doe')
    contact2 = Contact.objects.create(user=test_user, first_name='Jane',
                                      last_name='Smith')
    # Create contact for different user (should not appear)
    other_user = User.objects.create_user(username='other', password='testpass')
    Contact.objects.create(user=other_user, first_name='Other', last_name='User')
    response = client.get(reverse('contact_list'))
    assert response.status_code == 200
    assert 'accounts/contact_list.html' in [t.name for t in response.templates]
    contacts = response.context['contacts']
    assert contacts.count() == 2
    assert contact1 in contacts
    assert contact2 in contacts


# ===== ADD CONTACT VIEW TESTS =====

def test_add_contact_requires_login(client):
    """Test add contact requires authentication."""
    response = client.get(reverse('add_contact'))
    assert response.status_code == 302


@pytest.mark.django_db
def test_add_contact_get(client, test_user):
    """Test GET request to add contact page."""
    client.force_login(test_user)
    response = client.get(reverse('add_contact'))
    assert response.status_code == 200
    assert 'contact_form' in response.context
    assert 'phone_form' in response.context
    assert 'accounts/add_contact.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_add_contact_post_valid(client, test_user, contact_data, phone_data):
    """Test POST with valid contact data."""
    client.force_login(test_user)
    data = contact_data.copy()
    data.update({
        'phone-phone_type': phone_data['phone_type'],
        'phone-number': phone_data['number']
    })

    response = client.post(reverse('add_contact'), data)
    assert response.status_code == 302
    assert response.url == reverse('contact_list')

    # Contact should be created
    assert Contact.objects.filter(first_name='John').exists()
    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert 'added successfully' in str(messages[0])


@pytest.mark.django_db
def test_add_contact_post_invalid(client, test_user):
    """Test POST with invalid contact data."""
    client.force_login(test_user)
    data = {
        'first_name': '',  # Missing required field
        'last_name': 'Doe'
    }

    response = client.post(reverse('add_contact'), data)
    # Should show form with errors
    assert response.status_code == 200
    assert response.context['contact_form'].errors


# ===== CONTACT DETAIL VIEW TESTS =====

@pytest.mark.django_db
def test_contact_detail_requires_login(client, test_contact):
    """Test contact detail requires authentication."""
    response = client.get(
        reverse('contact_detail', kwargs={'contact_id': test_contact.id})
    )
    assert response.status_code == 302


@pytest.mark.django_db
def test_contact_detail_authenticated(client, test_contact):
    """Test viewing own contact detail."""
    client.force_login(test_contact.user)
    response = client.get(
        reverse('contact_detail', kwargs={'contact_id': test_contact.id})
    )

    assert response.status_code == 200
    assert 'contact' in response.context
    assert response.context['contact'] == test_contact
    assert 'accounts/contact_detail.html' in [t.name for t in response.templates]


@pytest.mark.django_db
def test_contact_detail_other_users_contact(client, test_user):
    """Test cannot view other user's contact (404)."""
    client.force_login(test_user)
    # Create contact for different user
    other_user = User.objects.create_user(username='other', password='testpass')
    other_contact = Contact.objects.create(
        user=other_user,
        first_name='Other',
        last_name='User'
    )

    # Try to access other user's contact
    response = client.get(
        reverse('contact_detail', kwargs={'contact_id': other_contact.id})
    )
    # Should return 404 (not found or permission denied)
    assert response.status_code == 404


# ===== EDIT CONTACT VIEW TESTS =====

@pytest.mark.django_db
def test_edit_contact_get(client, test_contact):
    """Test GET request to edit contact."""
    client.force_login(test_contact.user)
    response = client.get(
        reverse('edit_contact', kwargs={'contact_id': test_contact.id})
    )

    assert response.status_code == 200
    assert 'form' in response.context
    assert 'contact' in response.context
    assert response.context['contact'] == test_contact


@pytest.mark.django_db
def test_edit_contact_post_valid(client, test_contact):
    """Test POST with valid update data."""
    client.force_login(test_contact.user)
    data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': 'updated@example.com',
        'linkedin': 'https://linkedin.com/in/updated'
    }

    response = client.post(
        reverse('edit_contact', kwargs={'contact_id': test_contact.id}),
        data
    )
    assert response.status_code == 302
    # Should redirect to contact detail
    assert response.url == reverse('contact_detail',
                                   kwargs={'contact_id': test_contact.id})
    # Check contact was updated
    test_contact.refresh_from_db()
    assert test_contact.first_name == 'Updated'
    assert test_contact.email == 'updated@example.com'
    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert 'updated successfully' in str(messages[0])


@pytest.mark.django_db
def test_edit_contact_other_user_404(client, test_user):
    """Test cannot edit other user's contact."""
    client.force_login(test_user)
    other_user = User.objects.create_user(username='other', password='testpass')
    other_contact = Contact.objects.create(
        user=other_user,
        first_name='Other',
        last_name='User'
    )

    response = client.get(
        reverse('edit_contact', kwargs={'contact_id': other_contact.id})
    )
    assert response.status_code == 404


# ===== DELETE CONTACT VIEW TESTS =====

@pytest.mark.django_db
def test_delete_contact_get(client, test_contact):
    """Test GET request to delete confirmation page."""
    client.force_login(test_contact.user)
    response = client.get(
        reverse('delete_contact', kwargs={'contact_id': test_contact.id})
    )
    assert response.status_code == 200
    assert 'contact' in response.context
    assert response.context['contact'] == test_contact


@pytest.mark.django_db
def test_delete_contact_post(client, test_contact):
    """Test POST to delete contact."""
    client.force_login(test_contact.user)
    contact_id = test_contact.id

    response = client.post(
        reverse('delete_contact', kwargs={'contact_id': contact_id})
    )

    assert response.status_code == 302
    assert response.url == reverse('contact_list')

    # Contact should be deleted
    assert not Contact.objects.filter(id=contact_id).exists()

    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert 'deleted successfully' in str(messages[0])


# ===== ADD PHONE VIEW TESTS =====

@pytest.mark.django_db
def test_add_phone_get(client, test_contact):
    """Test GET request to add phone page."""
    client.force_login(test_contact.user)

    response = client.get(
        reverse('add_phone', kwargs={'contact_id': test_contact.id})
    )

    assert response.status_code == 200
    assert 'form' in response.context
    assert 'contact' in response.context
    assert response.context['contact'] == test_contact


@pytest.mark.django_db
def test_add_phone_post_valid(client, test_contact, phone_data):
    """Test POST with valid phone data."""
    client.force_login(test_contact.user)

    response = client.post(
        reverse('add_phone', kwargs={'contact_id': test_contact.id}),
        phone_data
    )

    assert response.status_code == 302
    # Should redirect to contact detail
    assert response.url == reverse('contact_detail',
                                   kwargs={'contact_id': test_contact.id})

    # Phone should be created
    assert PhoneNumber.objects.filter(contact=test_contact).exists()

    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert 'Phone number added' in str(messages[0])


# ===== EDIT PHONE VIEW TESTS =====

@pytest.mark.django_db
def test_edit_phone_get(client, test_contact, phone_data):
    """Test GET request to edit phone."""
    client.force_login(test_contact.user)

    phone = PhoneNumber.objects.create(contact=test_contact, **phone_data)

    response = client.get(
        reverse('edit_phone', kwargs={'phone_id': phone.id})
    )

    assert response.status_code == 200
    assert 'form' in response.context
    assert 'phone' in response.context
    assert 'contact' in response.context


@pytest.mark.django_db
def test_edit_phone_post_valid(client, test_contact, phone_data):
    """Test POST to update phone."""
    client.force_login(test_contact.user)

    phone = PhoneNumber.objects.create(contact=test_contact, **phone_data)

    updated_data = {
        'phone_type': 'home',
        'number': '+0987654321'
    }

    response = client.post(
        reverse('edit_phone', kwargs={'phone_id': phone.id}),
        updated_data
    )

    assert response.status_code == 302
    assert response.url == reverse('contact_detail',
                                   kwargs={'contact_id': test_contact.id})

    # Phone should be updated
    phone.refresh_from_db()
    assert phone.phone_type == 'home'
    assert phone.number == '+0987654321'


# ===== DELETE PHONE VIEW TESTS =====

@pytest.mark.django_db
def test_delete_phone_post(client, test_contact, phone_data):
    """Test POST to delete phone."""
    client.force_login(test_contact.user)

    phone = PhoneNumber.objects.create(contact=test_contact, **phone_data)

    response = client.post(
        reverse('delete_phone', kwargs={'phone_id': phone.id})
    )

    assert response.status_code == 302
    assert response.url == reverse('contact_detail',
                                   kwargs={'contact_id': test_contact.id})

    # Phone should be deleted
    assert not PhoneNumber.objects.filter(id=phone.id).exists()

    # Check success message
    messages = list(get_messages(response.wsgi_request))
    assert 'deleted' in str(messages[0])


# ===== INTEGRATION TESTS =====

@pytest.mark.django_db
def test_full_contact_workflow(client, test_user):
    """Test complete workflow: Add → View → Edit → Delete."""
    client.force_login(test_user)

    # 1. Add contact
    add_data = {
        'first_name': 'Workflow',
        'last_name': 'Test',
        'email': 'workflow@test.com'
    }
    response = client.post(reverse('add_contact'), add_data)
    assert response.status_code == 302

    # Get the created contact
    contact = Contact.objects.get(first_name='Workflow')

    # 2. View contact
    response = client.get(
        reverse('contact_detail', kwargs={'contact_id': contact.id})
    )
    assert response.status_code == 200

    # 3. Edit contact
    edit_data = {
        'first_name': 'Updated',
        'last_name': 'Workflow',
        'email': 'updated@test.com'
    }
    response = client.post(
        reverse('edit_contact', kwargs={'contact_id': contact.id}),
        edit_data
    )
    assert response.status_code == 302

    # 4. Delete contact
    response = client.post(
        reverse('delete_contact', kwargs={'contact_id': contact.id})
    )
    assert response.status_code == 302

    # Contact should be gone
    assert not Contact.objects.filter(id=contact.id).exists()
