import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class TenantManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        tenant = self.model(email=email, name=name, **extra_fields)
        if password:
            tenant.set_password(password)
        tenant.save(using=self._db)
        return tenant

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)

class Tenant(AbstractBaseUser, PermissionsMixin):
    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('scale', 'Scale'),
        ('enterprise', 'Enterprise'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField()
    email = models.EmailField(unique=True, max_length=320, db_index=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='starter')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    llm_provider = models.CharField(max_length=50, default='openai')
    llm_model = models.CharField(max_length=100, default='gpt-4o-mini')
    llm_api_key = models.CharField(max_length=255, null=True, blank=True)
    llm_base_url = models.CharField(max_length=255, null=True, blank=True)
    
    objects = TenantManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return f"{self.name} ({self.email})"

class Namespace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='namespaces')
    name = models.CharField(max_length=64, db_index=True)
    doc_count = models.IntegerField(default=0)
    token_count = models.BigIntegerField(default=0)
    
    llm_provider = models.CharField(max_length=50, default='openai')
    llm_model = models.CharField(max_length=100, default='gpt-4o-mini')
    llm_api_key = models.CharField(max_length=255, null=True, blank=True)
    llm_base_url = models.CharField(max_length=255, null=True, blank=True)
    
    embedding_provider = models.CharField(max_length=50, default='dashscope')
    embedding_model = models.CharField(max_length=100, default='text-embedding-v4')
    embedding_api_key = models.CharField(max_length=255, null=True, blank=True)
    embedding_base_url = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('tenant', 'name')
        
    def __str__(self):
        return self.name

class ApiKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='api_keys')
    key_hash = models.TextField(unique=True)
    prefix = models.CharField(max_length=50, db_index=True)
    label = models.CharField(max_length=100, null=True, blank=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, default='admin')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.prefix

class Document(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
        ('md', 'MD'),
        ('pptx', 'PPTX'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    namespace = models.ForeignKey(Namespace, on_delete=models.CASCADE, related_name='documents')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    chunk_count = models.IntegerField(default=0)
    images_inside = models.BooleanField(default=False)
    s3_key = models.TextField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['namespace', '-created_at']),
        ]

    def __str__(self):
        return self.filename

class UsageEvent(models.Model):
    EVENT_CHOICES = [
        ('query', 'Query'),
        ('ingest', 'Ingest'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='usage_events')
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES, db_index=True)
    tokens_used = models.IntegerField(default=0)
    query_ms = models.IntegerField(null=True, blank=True)
    model_used = models.CharField(max_length=50, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.event_type} - {self.tokens_used}"
