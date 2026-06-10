from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # Allow either cookie or header for API usability
        raw_token = request.COOKIES.get('access_token') or request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        if not raw_token:
            return None
            
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception:
            return None
from rest_framework.permissions import BasePermission
from ragaas.models import ApiKey
from core.security import verify_api_key

class ApiKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer rgs_live_'):
            return None
            
        raw_key = auth_header.split(' ')[1]
        
        # Extract the display prefix to perform an O(1) indexed lookup
        # The stored prefix format is 'rgs_live_' + 8 chars + '...'
        # _KEY_PREFIX = "rgs_live_"
        # _PREFIX_DISPLAY_LENGTH = 8
        prefix_str = "rgs_live_"
        if raw_key.startswith(prefix_str):
            random_part = raw_key[len(prefix_str):]
            display_prefix = f"{prefix_str}{random_part[:8]}..."
            
            api_key = ApiKey.objects.filter(prefix=display_prefix, is_active=True).select_related('tenant').first()
            if api_key and verify_api_key(raw_key, api_key.key_hash):
                from django.utils import timezone
                api_key.last_used = timezone.now()
                api_key.save(update_fields=['last_used'])
                
                return (api_key.tenant, api_key)
                
        raise exceptions.AuthenticationFailed('Invalid API Key')

class CanDeployApiPermission(BasePermission):
    """
    Allows access only if the user is using a dashboard session (JWT) 
    OR their active plan allows API deployment (using ApiKey).
    """
    message = "External API access is not available on the Free plan. Please upgrade your subscription."
    
    def has_permission(self, request, view):
        # If the auth object is an ApiKey, it means they are accessing via external API
        if isinstance(request.auth, ApiKey):
            return request.user.can_deploy_api
            
        # Otherwise, they are using a JWT token from the dashboard
        return True
