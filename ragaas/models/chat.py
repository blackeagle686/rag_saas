import uuid
from django.db import models
from ragaas.models.core import Tenant, Namespace

class EndUser(models.Model):
    """Django ORM Model for EndUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='end_users')
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    platform = models.CharField(max_length=50, default='web_widget')
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'external_id')

class ChatSession(models.Model):
    """Django ORM Model for ChatSession"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    end_user = models.ForeignKey(EndUser, on_delete=models.CASCADE, related_name='sessions')
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ChatMessage(models.Model):
    """Django ORM Model for ChatMessage"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20)  # user, assistant, system
    content = models.TextField()
    tokens_used = models.IntegerField(default=0)
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
