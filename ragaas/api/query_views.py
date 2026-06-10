from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ragaas.models import Namespace, Document
from ragaas.services import NamespaceService, QueryService
from ragaas.security.authentication import ApiKeyAuthentication, CanDeployApiPermission
from ragaas.security.throttling import TierRateThrottle
from ragaas.workers.tasks import process_document

class IngestView(views.APIView):
    authentication_classes = [ApiKeyAuthentication, *views.APIView.authentication_classes]
    permission_classes = (IsAuthenticated, CanDeployApiPermission)
    throttle_classes = (TierRateThrottle,)
    
    def post(self, request):
        file_obj = request.FILES.get('file')
        namespace_name = request.data.get('namespace', 'default')
        
        if not file_obj:
            return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)
            
        ns, _ = NamespaceService.create_namespace(request.user, {'name': namespace_name})
        
        doc = Document.objects.create(
            namespace=ns,
            filename=file_obj.name,
            file_type=file_obj.name.split('.')[-1].lower() if '.' in file_obj.name else 'txt',
            status='pending'
        )
        
        import os
        from django.conf import settings
        storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        dest_dir = os.path.join(storage_path, request.user.id.hex, str(ns.id))
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{doc.id}.{doc.file_type}")
        
        with open(dest_path, 'wb+') as dest:
            for chunk in file_obj.chunks():
                dest.write(chunk)
                
        doc.s3_key = dest_path
        doc.save()
        
        process_document.delay(str(doc.id))
        
        return Response({
            "document_id": doc.id,
            "status": doc.status,
            "message": "Document queued for processing"
        }, status=status.HTTP_202_ACCEPTED)

class QueryView(views.APIView):
    authentication_classes = [ApiKeyAuthentication, *views.APIView.authentication_classes]
    permission_classes = (IsAuthenticated, CanDeployApiPermission)
    throttle_classes = (TierRateThrottle,)

    def post(self, request):
        namespace_name = request.data.get('namespace', 'default')
        query_text = request.data.get('query')
        top_k = int(request.data.get('top_k', 3))
        custom_model = request.data.get('model')
        
        if not query_text:
            return Response({"detail": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
            
        service = QueryService()
        try:
            result = service.query(request.user, namespace_name, query_text, top_k, custom_model)
            return Response(result)
        except Namespace.DoesNotExist:
            return Response({"detail": "Namespace not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
