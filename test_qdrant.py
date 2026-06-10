import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from qdrant_client import QdrantClient
from django.conf import settings
from ragaas.models import Document

if hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY:
    qdrant = QdrantClient(url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}", api_key=settings.QDRANT_API_KEY, check_compatibility=False)
else:
    qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)

collections = qdrant.get_collections().collections
for col in collections:
    print("Collection:", col.name)
    info = qdrant.get_collection(col.name)
    print("Points count:", info.points_count)
