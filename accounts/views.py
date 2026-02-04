from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Contact, PhoneNumber
from .contact_forms import ContactForm, PhoneNumberForm

@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html', {'user': request.user})

def user_logout(request):
    logout(request)  # This logs the user out
    return redirect('login')  # Redirect to login page
    
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def contact_list(request):
    contacts = Contact.objects.filter(user=request.user)
    return render(request, 'accounts/contact_list.html', {'contacts': contacts})

@login_required
def add_contact(request):
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        phone_form = PhoneNumberForm(request.POST, prefix='phone')
        
        if contact_form.is_valid():
            contact = contact_form.save(commit=False)
            contact.user = request.user
            contact.save()
            
            # Save phone if provided
            if phone_form.is_valid() and phone_form.cleaned_data.get('number'):
                phone = phone_form.save(commit=False)
                phone.contact = contact
                phone.save()
            
        
            messages.success(request, f'Contact {contact.first_name} added successfully!')
            return redirect('contact_list')
    
    else:
        contact_form = ContactForm()
        phone_form = PhoneNumberForm(prefix='phone')
    
    return render(request, 'accounts/add_contact.html', {
        'contact_form': contact_form,
        'phone_form': phone_form,
    })

@login_required
def contact_detail(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    return render(request, 'accounts/contact_detail.html', {'contact': contact})

@login_required
def add_phone(request, contact_id):
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
    return render(request, 'accounts/add_phone.html', {'form': form, 'contact': contact})


@login_required
def edit_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contact {contact.first_name} updated successfully!')
            return redirect('contact_detail', contact_id=contact.id)
    else:
        form = ContactForm(instance=contact)
    
    return render(request, 'accounts/edit_contact.html', {'form': form, 'contact': contact})


@login_required
def delete_contact(request, contact_id):
    contact = get_object_or_404(Contact, id=contact_id, user=request.user)
    
    if request.method == 'POST':
        contact_name = contact.first_name
        contact.delete()
        messages.success(request, f'Contact {contact_name} deleted successfully!')
        return redirect('contact_list')
    
    return render(request, 'accounts/delete_contact.html', {'contact': contact})

@login_required
def edit_phone(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, contact__user=request.user)
    contact = phone.contact
    
    if request.method == 'POST':
        form = PhoneNumberForm(request.POST, instance=phone)
        if form.is_valid():
            form.save()
            messages.success(request, 'Phone number updated!')
            return redirect('contact_detail', contact_id=contact.id)
    else:
        form = PhoneNumberForm(instance=phone)
    
    return render(request, 'accounts/edit_phone.html', {'form': form, 'phone': phone, 'contact': contact})


@login_required
def delete_phone(request, phone_id):
    phone = get_object_or_404(PhoneNumber, id=phone_id, contact__user=request.user)
    contact = phone.contact
    
    if request.method == 'POST':
        phone_number = phone.number
        phone.delete()
        messages.success(request, f'Phone number {phone_number} deleted!')
        return redirect('contact_detail', contact_id=contact.id)
    
    return render(request, 'accounts/delete_phone.html', {'phone': phone, 'contact': contact})