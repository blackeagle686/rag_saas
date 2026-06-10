from ragaas.models import Namespace, ApiKey
from core.security import generate_api_key

class KeyService:
    @staticmethod
    def create_key(tenant, label, role="admin", namespace_name=None):
        raw_key, key_hash, prefix = generate_api_key("rgs_live_")
        
        ns = None
        if namespace_name:
            ns = Namespace.objects.get(tenant=tenant, name=namespace_name)
            
        api_key = ApiKey.objects.create(
            tenant=tenant,
            key_hash=key_hash,
            prefix=prefix,
            label=label,
            role=role,
            namespace=ns
        )
        return raw_key, api_key
