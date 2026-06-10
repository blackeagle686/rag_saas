from rest_framework import generics, status, views, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ragaas.models import Namespace, Document, ApiKey
from ragaas.api.serializers.core import NamespaceSerializer, NamespaceCreateSerializer, DocumentSerializer, ApiKeySerializer
from ragaas.services import NamespaceService, KeyService

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
