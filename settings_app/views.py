from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from accounts.models import UserProfile
from .forms import UserUpdateForm, ProfileUpdateForm
import requests
import json

@login_required
def index(request):
    """
    Renders and processes the profile information, secure password resets,
    Mistral API Key inputs, and light/dark dashboard settings.
    """
    profile = request.user.userprofile
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Save state and mark unsaved changes as resolved
            profile.has_unsaved_changes = False
            profile.save()
            
            messages.success(request, "Profile settings updated successfully!")
            return redirect('settings_app:index')
        else:
            messages.error(request, "Failed to update settings. Please check your form fields.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
        
    return render(request, 'settings_app/index.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def toggle_theme(request):
    """
    AJAX endpoint called when toggling Light/Dark theme. Persists preference in DB.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            theme = data.get('theme', 'light')
            if theme in ['light', 'dark']:
                profile = request.user.userprofile
                profile.theme_preference = theme
                profile.save()
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


@login_required
def test_mistral_connection(request):
    """
    AJAX POST endpoint to test connection validity of the Mistral AI API key.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=400)
        
    api_key = request.POST.get('api_key')
    if not api_key:
        # Fallback to already saved key
        api_key = request.user.userprofile.mistral_api_key
        
    if not api_key:
        return JsonResponse({'status': 'error', 'message': 'API Key cannot be blank.'}, status=400)
        
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    # Send a tiny query to verify token is valid
    payload = {
        "model": "open-mistral-7b",
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=8)
        if response.status_code == 200:
            return JsonResponse({
                'status': 'success', 
                'message': 'API Connection verified successfully! Mistral is active.'
            })
        else:
            err_msg = "Invalid authorization or plan restrictions."
            try:
                err_data = response.json()
                err_msg = err_data.get('message', err_msg)
            except Exception:
                pass
            return JsonResponse({
                'status': 'error', 
                'message': f"Mistral API error (HTTP {response.status_code}): {err_msg}"
            })
    except requests.exceptions.Timeout:
        return JsonResponse({'status': 'error', 'message': 'Connection timed out. Check internet settings.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Connection failed: {str(e)}'})
