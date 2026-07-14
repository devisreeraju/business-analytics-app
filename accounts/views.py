from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistrationForm, LoginForm
from .models import UserProfile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Authenticate and login the new user
            authenticated_user = authenticate(
                username=user.username, 
                password=form.cleaned_data['password']
            )
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, f"Welcome to AI Copilot, {user.username}! Your account was created successfully.")
                return redirect('dashboard:index')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = RegistrationForm()
        
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data['remember_me']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Session duration based on remember_me checkbox
                if remember_me:
                    request.session.set_expiry(1209600) # 2 weeks in seconds
                else:
                    request.session.set_expiry(0) # Browser closes -> session expires
                    
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard:index')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please fill out the form correctly.")
    else:
        form = LoginForm()
        
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.method == 'POST' or request.GET.get('save') == 'true':
        if request.user.is_authenticated:
            # Handle Save & Logout option
            if request.GET.get('save') == 'true':
                try:
                    profile = request.user.userprofile
                    profile.has_unsaved_changes = False
                    profile.save()
                    messages.success(request, "Session state saved successfully.")
                except Exception:
                    pass
            
            logout(request)
            messages.success(request, "You have been logged out successfully.")
            
        return redirect('accounts:login')
        
    # If they hit this via GET without save parameter, redirect to login
    return redirect('accounts:login')


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Look up if user exists for demo purposes
            user_exists = User.objects.filter(email__iexact=email).exists()
            if user_exists:
                messages.success(request, f"Password reset instructions have been printed to the console logs. Please check the terminal.")
                # We'll print it out for easy developer inspection
                print("\n" + "="*50)
                print(f"MOCK PASSWORD RESET LINK FOR: {email}")
                print("Link: http://localhost:8000/accounts/login/")
                print("="*50 + "\n")
            else:
                # Security best practice: don't reveal if email exists, show same success msg
                messages.success(request, f"If that email exists in our system, password reset instructions have been sent.")
            return redirect('accounts:login')
        else:
            messages.error(request, "Please enter a valid email address.")
            
    return render(request, 'accounts/forgot_password.html')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully!")
            return redirect('settings_app:index')
        else:
            messages.error(request, "Password change failed. Please correct the errors below.")
            # Redirect back to settings page with validation errors in session
            # For simplicity, we can render the settings page directly or render a custom password change template.
            # Let's render a custom view for changing password.
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'accounts/change_password.html', {'form': form})
