def copilot_context(request):
    """
    Exposes global variables to all templates for the Copilot application,
    including the active dataset, user theme preference, unsaved status,
    and whether Mistral AI is configured.
    """
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            theme = profile.theme_preference
            unsaved = profile.has_unsaved_changes
            mistral_api_key = profile.mistral_api_key
            has_mistral = bool(mistral_api_key)
        except Exception:
            theme = 'light'
            unsaved = False
            has_mistral = False
        
        try:
            from datasets.models import Dataset
            active_ds = Dataset.objects.filter(user=request.user, is_active=True).first()
        except Exception:
            active_ds = None
        
        return {
            'theme_preference': theme,
            'has_unsaved_changes': unsaved,
            'mistral_configured': has_mistral,
            'active_dataset': active_ds,
        }
    return {
        'theme_preference': 'light',
        'has_unsaved_changes': False,
        'mistral_configured': False,
        'active_dataset': None,
    }
