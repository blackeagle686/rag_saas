from rest_framework.throttling import SimpleRateThrottle

class TierRateThrottle(SimpleRateThrottle):
    """
    Dynamically limits API requests based on the tenant's subscription plan.
    Enforces the rate limits defined in the monetization strategy.
    """
    scope = 'tenant_tier'
    
    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.id
            }
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated:
            plan = getattr(request.user, 'plan', 'free')
            
            # Rate limits as defined in the monetization plan
            rates = {
                'free': '10/day',
                'start': '10/minute',
                'mid': '50/minute',
                'prime': '200/minute',
                'enterprise': '1000/minute'
            }
            
            self.rate = rates.get(plan, '10/day')
            self.num_requests, self.duration = self.parse_rate(self.rate)
            
        return super().allow_request(request, view)
