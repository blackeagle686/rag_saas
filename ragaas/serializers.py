from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import Namespace, Document, ApiKey, UsageEvent

Tenant = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('name', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class TenantSettingsSerializer(serializers.ModelSerializer):
    llm_api_key = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ('llm_provider', 'llm_model', 'llm_api_key', 'llm_base_url')

    def get_llm_api_key(self, obj):
        key = obj.llm_api_key or ""
        if key:
            if len(key) > 10:
                return f"{key[:6]}...{key[-4:]}"
            return "********"
        return ""

class TenantSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('llm_provider', 'llm_model', 'llm_api_key', 'llm_base_url')

class NamespaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = (
            'id', 'name', 'doc_count', 'token_count', 
            'llm_provider', 'llm_model', 
            'embedding_provider', 'embedding_model', 'created_at'
        )

class NamespaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Namespace
        fields = (
            'name', 'llm_provider', 'llm_model', 'llm_api_key', 'llm_base_url',
            'embedding_provider', 'embedding_model', 'embedding_api_key', 'embedding_base_url'
        )

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'filename', 'file_type', 'status', 'chunk_count', 'created_at', 'error_message')

class ApiKeySerializer(serializers.ModelSerializer):
    namespace_name = serializers.CharField(source='namespace.name', read_only=True)
    
    class Meta:
        model = ApiKey
        fields = ('id', 'prefix', 'label', 'created_at', 'last_used', 'role', 'namespace_name')
