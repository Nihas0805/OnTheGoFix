
from myapp.models import ServiceProviderProfile

def service_provider_profile_picture(request):
    if request.user.is_authenticated and request.user.role == 'provider':
        try:
            profile_picture = request.user.provider_profile.profile_picture.url
        except ServiceProviderProfile.DoesNotExist:
            profile_picture = 'default/path/to/default_profile_picture.png' 
        return {'service_provider_profile_picture': profile_picture}
    return {'service_provider_profile_picture': None}
