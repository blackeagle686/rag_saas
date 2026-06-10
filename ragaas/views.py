from rest_framework import generics, status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.shortcuts import get_object_or_404
from .models import Namespace, Document, ApiKey, Tenant
from .serializers import (
    RegisterSerializer, TenantSettingsSerializer, TenantSettingsUpdateSerializer,
    NamespaceSerializer, NamespaceCreateSerializer, DocumentSerializer, ApiKeySerializer
)
from .services import KeyService, NamespaceService, QueryService
from .tasks import process_document

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    queryset = Tenant.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "token_type": "bearer",
            "user": serializer.data
        }, status=status.HTTP_201_CREATED)

class LoginView(views.APIView):
    permission_classes = (AllowAny,)
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "token_type": "bearer"
            })
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class TenantSettingsView(views.APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = TenantSettingsSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = TenantSettingsUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TenantSettingsSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NamespaceViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    lookup_field = 'name'

    def get_queryset(self):
        return Namespace.objects.filter(tenant=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"namespaces": serializer.data})

    def get_serializer_class(self):
        if self.action == 'create':
            return NamespaceCreateSerializer
        return NamespaceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ns, created = NamespaceService.create_namespace(request.user, serializer.validated_data)
        if not created:
            return Response({"detail": f"Namespace '{ns.name}' already exists."}, status=status.HTTP_409_CONFLICT)
        return Response(NamespaceSerializer(ns).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        confirm = request.data.get('confirm', False)
        if str(confirm).lower() != 'true':
            return Response({"detail": "You must set 'confirm: true' to delete a namespace."}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
            
        ns = self.get_object()
        NamespaceService.delete_namespace(request.user, ns.name)
        return Response({"message": f"Namespace '{ns.name}' and all its data have been deleted."}, status=status.HTTP_200_OK)

class NamespaceDocumentListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DocumentSerializer

    def get_queryset(self):
        name = self.kwargs['name']
        ns = get_object_or_404(Namespace, tenant=self.request.user, name=name)
        return Document.objects.filter(namespace=ns).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"documents": serializer.data})

class ApiKeyViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ApiKeySerializer

    def get_queryset(self):
        return ApiKey.objects.filter(tenant=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"keys": serializer.data})

    def create(self, request, *args, **kwargs):
        label = request.data.get('label', 'Unnamed Key')
        role = request.data.get('role', 'admin')
        namespace_name = request.data.get('namespace')
        
        raw_key, api_key = KeyService.create_key(request.user, label, role, namespace_name)
        
        return Response({
            "key": raw_key,
            "prefix": api_key.prefix,
            "label": api_key.label,
            "id": api_key.id
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        api_key = self.get_object()
        api_key.delete()
        return Response({"message": f"API key {api_key.id} has been revoked."}, status=status.HTTP_200_OK)

class IngestView(views.APIView):
    permission_classes = (IsAuthenticated,)
    
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
    permission_classes = (IsAuthenticated,)

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
