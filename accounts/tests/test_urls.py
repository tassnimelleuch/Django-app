"""
Tests for URL routing in the accounts app.
"""

import pytest
from django.urls import reverse, resolve
from django.contrib.auth import views as auth_views
from django.test import Client

# pylint: disable=comparison-with-callable
from accounts import views


@pytest.mark.django_db
def test_register_url_resolves():
    """Register URL resolves to correct view."""
    path = reverse("register")
    assert path == "/register/"

    resolver = resolve("/register/")
    assert resolver.func == views.register
    assert resolver.url_name == "register"


@pytest.mark.django_db
def test_login_url_resolves():
    """Login URL resolves to Django LoginView."""
    path = reverse("login")
    assert path == "/login/"

    resolver = resolve("/login/")
    assert resolver.func.view_class == auth_views.LoginView
    assert resolver.url_name == "login"


@pytest.mark.django_db
def test_logout_url_resolves():
    """Logout URL resolves to logout view."""
    path = reverse("logout")
    assert path == "/logout/"

    resolver = resolve("/logout/")
    assert resolver.func == views.user_logout
    assert resolver.url_name == "logout"


@pytest.mark.django_db
def test_dashboard_url_resolves():
    """Dashboard URL resolves correctly."""
    path = reverse("dashboard")
    assert path == "/dashboard/"

    resolver = resolve("/dashboard/")
    assert resolver.func == views.dashboard
    assert resolver.url_name == "dashboard"


@pytest.mark.django_db
def test_contact_list_url_resolves():
    """Contact list URL resolves correctly."""
    path = reverse("contact_list")
    assert path == "/contacts/"

    resolver = resolve("/contacts/")
    assert resolver.func == views.contact_list
    assert resolver.url_name == "contact_list"


@pytest.mark.django_db
def test_add_contact_url_resolves():
    """Add contact URL resolves correctly."""
    path = reverse("add_contact")
    assert path == "/contacts/add/"

    resolver = resolve("/contacts/add/")
    assert resolver.func == views.add_contact
    assert resolver.url_name == "add_contact"


@pytest.mark.django_db
def test_contact_detail_url_resolves():
    """Contact detail URL resolves with ID."""
    resolver = resolve("/contacts/123/")
    assert resolver.func == views.contact_detail
    assert resolver.url_name == "contact_detail"
    assert resolver.kwargs == {"contact_id": 123}

    path = reverse("contact_detail", kwargs={"contact_id": 456})
    assert path == "/contacts/456/"


@pytest.mark.django_db
def test_edit_contact_url_resolves():
    """Edit contact URL resolves with ID."""
    resolver = resolve("/contacts/789/edit/")
    assert resolver.func == views.edit_contact
    assert resolver.url_name == "edit_contact"
    assert resolver.kwargs == {"contact_id": 789}

    path = reverse("edit_contact", kwargs={"contact_id": 999})
    assert path == "/contacts/999/edit/"


@pytest.mark.django_db
def test_delete_contact_url_resolves():
    """Delete contact URL resolves with ID."""
    resolver = resolve("/contacts/111/delete/")
    assert resolver.func == views.delete_contact
    assert resolver.url_name == "delete_contact"
    assert resolver.kwargs == {"contact_id": 111}

    path = reverse("delete_contact", kwargs={"contact_id": 222})
    assert path == "/contacts/222/delete/"


@pytest.mark.django_db
def test_add_phone_url_resolves():
    """Add phone URL resolves with contact ID."""
    resolver = resolve("/contacts/333/add-phone/")
    assert resolver.func == views.add_phone
    assert resolver.url_name == "add_phone"
    assert resolver.kwargs == {"contact_id": 333}

    path = reverse("add_phone", kwargs={"contact_id": 444})
    assert path == "/contacts/444/add-phone/"


@pytest.mark.django_db
def test_edit_phone_url_resolves():
    """Edit phone URL resolves with phone ID."""
    resolver = resolve("/phone/555/edit/")
    assert resolver.func == views.edit_phone
    assert resolver.url_name == "edit_phone"
    assert resolver.kwargs == {"phone_id": 555}

    path = reverse("edit_phone", kwargs={"phone_id": 666})
    assert path == "/phone/666/edit/"


@pytest.mark.django_db
def test_delete_phone_url_resolves():
    """Delete phone URL resolves with phone ID."""
    resolver = resolve("/phone/777/delete/")
    assert resolver.func == views.delete_phone
    assert resolver.url_name == "delete_phone"
    assert resolver.kwargs == {"phone_id": 777}

    path = reverse("delete_phone", kwargs={"phone_id": 888})
    assert path == "/phone/888/delete/"


@pytest.mark.django_db
def test_all_url_names():
    """All URL names reverse correctly."""
    url_tests = (
        ("register", "/register/"),
        ("login", "/login/"),
        ("logout", "/logout/"),
        ("dashboard", "/dashboard/"),
        ("contact_list", "/contacts/"),
        ("add_contact", "/contacts/add/"),
    )

    for name, expected_path in url_tests:
        assert reverse(name) == expected_path


@pytest.mark.django_db
def test_url_patterns_with_ids():
    """URL patterns requiring IDs reverse correctly."""
    id_url_tests = (
        ("contact_detail", {"contact_id": 1}, "/contacts/1/"),
        ("edit_contact", {"contact_id": 2}, "/contacts/2/edit/"),
        ("delete_contact", {"contact_id": 3}, "/contacts/3/delete/"),
        ("add_phone", {"contact_id": 4}, "/contacts/4/add-phone/"),
        ("edit_phone", {"phone_id": 5}, "/phone/5/edit/"),
        ("delete_phone", {"phone_id": 6}, "/phone/6/delete/"),
    )

    for name, kwargs, expected_path in id_url_tests:
        assert reverse(name, kwargs=kwargs) == expected_path


@pytest.mark.django_db
def test_invalid_url_returns_404():
    """Non-existent URLs return 404."""
    client = Client()

    invalid_urls = (
        "/nonexistent/",
        "/contacts/invalid/",
        "/contacts/abc/edit/",
        "/phone/xyz/delete/",
    )

    for url in invalid_urls:
        response = client.get(url)
        assert response.status_code == 404
