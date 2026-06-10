import os
import shutil

# 1. Create directories
dirs = ['ragaas/api', 'ragaas/api/serializers', 'ragaas/services', 'ragaas/security', 'ragaas/workers', 'ragaas/models']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    with open(f"{d}/__init__.py", "w") as f:
        pass

# 2. Move single files
if os.path.exists('ragaas/authentication.py'):
    shutil.move('ragaas/authentication.py', 'ragaas/security/authentication.py')
if os.path.exists('ragaas/throttling.py'):
    shutil.move('ragaas/throttling.py', 'ragaas/security/throttling.py')
if os.path.exists('ragaas/tasks.py'):
    shutil.move('ragaas/tasks.py', 'ragaas/workers/tasks.py')
if os.path.exists('ragaas/serializers.py'):
    shutil.move('ragaas/serializers.py', 'ragaas/api/serializers/core.py')
if os.path.exists('ragaas/billing.py'):
    shutil.move('ragaas/billing.py', 'ragaas/api/billing_views.py')
if os.path.exists('ragaas/models.py'):
    shutil.move('ragaas/models.py', 'ragaas/models/core.py')

# Fix models/__init__.py so Django still finds them
with open('ragaas/models/__init__.py', 'w') as f:
    f.write("from .core import Tenant, Namespace, Document, ApiKey, UsageEvent\n")

print("Files moved successfully.")
