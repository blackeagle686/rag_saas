from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, LogoutView, TenantSettingsView, NamespaceViewSet, NamespaceDocumentListView,
    ApiKeyViewSet, IngestView, QueryView
)
from .billing import CreateCheckoutSessionView, StripeWebhookView

router = DefaultRouter(trailing_slash=False)
router.register(r'namespaces', NamespaceViewSet, basename='namespace')
router.register(r'keys', ApiKeyViewSet, basename='apikey')

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='auth_register'),
    path('auth/login', LoginView.as_view(), name='auth_login'),
    path('auth/logout', LogoutView.as_view(), name='auth_logout'),
    
    path('tenant/settings', TenantSettingsView.as_view(), name='tenant-settings'),
    
    path('namespaces/<str:name>/docs', NamespaceDocumentListView.as_view(), name='namespace-docs'),
    
    path('ingest', IngestView.as_view(), name='ingest'),
    path('query', QueryView.as_view(), name='query'),
    
    path('billing/checkout', CreateCheckoutSessionView.as_view(), name='billing-checkout'),
    path('billing/webhook', StripeWebhookView.as_view(), name='billing-webhook'),
    
    path('', include(router.urls)),
]
