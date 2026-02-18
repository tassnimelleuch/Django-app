"""Views for user account management, authentication, and contact management."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_safe, require_http_methods
from django.views.decorators.csrf import csrf_protect
from .forms import RegisterForm
from .models import Contact, PhoneNumber
from .contact_forms import ContactForm, PhoneNumberForm

# SAFE METHODS (GET, HEAD, OPTIONS) - No CSRF needed
@login_required
@require_safe
def dashboard(request):
    """Display the user's dashboard."""
    return render(request, 'accounts/dashboard.html', {'user': request.user})


# UNSAFE METHODS - All POST-only views have CSRF protection via global middleware
@require_http_methods(['POST'])
@csrf_protect
def user_logout(request):
    """Log the user out and redirect to login page."""
    logout(request)
    return redirect('login')


@require_http_methods(['GET', 'POST'])
@csrf_protect
def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(
                request,
                f'Account created for {username}! You can now log in.'
            )
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_safe
def contact_list(request):
    """Display a list of all contacts for the logged-in user."""
    contacts = Contact.objects.filter(user=request.user)
    return render(request, 'accounts/contact_list.html', {'contacts': contacts})


@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def add_contact(request):
    """Handle adding a new contact."""
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        phone_form = PhoneNumberForm(request.POST, prefix='phone')

        if contact_form.is_valid():
            contact = contact_form.save(commit=False)
            contact.user = request.user
            contact.save()

            if phone_form.is_valid() and phone_form.cleaned_data.get('number'):
                phone = phone_form.save(commit=False)
                phone.contact = contact
                phone.save()

            messages.success(
                request,
                f'Contact {contact.first_name} added successfully!'
            )
            return redirect('contact_list')
    else:
        contact_form = ContactForm()
        phone_form = PhoneNumberForm(prefix='phone')

    return render(request, 'accounts/add_contact.html', {
        'contact_form': contact_form,
        'phone_form': phone_form,
    })


@login_required
@require_safe
def contact_detail(request, contact_id):
    """Display details for a specific contact."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    return render(request, 'accounts/contact_detail.html', {'contact': contact})


@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def add_phone(request, contact_id):
    """Handle adding a phone number to a contact."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone = form.save(commit=False)
            phone.contact = contact
            phone.save()
            messages.success(request, 'Phone number added!')
            return redirect('contact_detail', contact_id=contact.id)
    else:
        form = PhoneNumberForm()
    return render(
        request,
        'accounts/add_phone.html',
        {'form': form, 'contact': contact}
    )


@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def edit_contact(request, contact_id):
    """Handle editing a contact."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Contact {contact.first_name} updated successfully!'
            )
            return redirect('contact_detail', contact_id=contact.id)
    else:
        form = ContactForm(instance=contact)

    return render(
        request,
        'accounts/edit_contact.html',
        {'form': form, 'contact': contact}
    )


@login_required
@require_http_methods(['POST'])
@csrf_protect
def delete_contact(request, contact_id):
    """Handle deleting a contact."""
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    contact_name = contact.first_name
    contact.delete()
    messages.success(
        request,
        f'Contact {contact_name} deleted successfully!'
    )
    return redirect('contact_list')


@login_required
@require_http_methods(['GET', 'POST'])
@csrf_protect
def edit_phone(request, phone_id):
    """Handle editing a phone number."""
    phone = get_object_or_404(
        PhoneNumber,
        id=phone_id,
        contact__user=request.user
    )
    contact = phone.contact

    if request.method == 'POST':
        form = PhoneNumberForm(request.POST, instance=phone)
        if form.is_valid():
            form.save()
            messages.success(request, 'Phone number updated!')
            return redirect('contact_detail', contact_id=contact.id)
    else:
        form = PhoneNumberForm(instance=phone)

    return render(
        request,
        'accounts/edit_phone.html',
        {'form': form, 'phone': phone, 'contact': contact}
    )


@login_required
@require_http_methods(['POST'])
@csrf_protect
def delete_phone(request, phone_id):
    """Handle deleting a phone number."""
    phone = get_object_or_404(
        PhoneNumber,
        id=phone_id,
        contact__user=request.user
    )
    contact = phone.contact
    phone_number = phone.number
    phone.delete()
    messages.success(
        request,
        f'Phone number {phone_number} deleted!'
    )
    return redirect('contact_detail', contact_id=contact.id)
