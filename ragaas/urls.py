from django.urls import path, include
from rest_framework.routers import DefaultRouter

from ragaas.api.auth_views import RegisterView, LoginView, LogoutView, TenantSettingsView
from ragaas.api.namespace_views import NamespaceViewSet, NamespaceDocumentListView, ApiKeyViewSet
from ragaas.api.query_views import IngestView, QueryView, DatabaseIngestView
from ragaas.api.billing_views import CreateCheckoutSessionView, StripeWebhookView, MockCheckoutSuccessView
from ragaas.api.chat_views import SharedBotChatView

router = DefaultRouter(trailing_slash=False)
router.register(r'namespaces', NamespaceViewSet, basename='namespace')
router.register(r'keys', ApiKeyViewSet, basename='apikey')

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='auth_register'),
    path('auth/login', LoginView.as_view(), name='auth_login'),
    path('auth/logout', LogoutView.as_view(), name='auth_logout'),
    
    path('tenant/settings', TenantSettingsView.as_view(), name='tenant-settings'),
    
    path('namespaces/<str:name>/documents', NamespaceDocumentListView.as_view(), name='namespace-documents'),
    
    path('ingest', IngestView.as_view(), name='ingest'),
    path('ingest/database', DatabaseIngestView.as_view(), name='ingest-database'),
    path('query', QueryView.as_view(), name='query'),
    
    path('bot/<str:namespace_id>/chat', SharedBotChatView.as_view(), name='bot-chat'),
    
    path('billing/checkout', CreateCheckoutSessionView.as_view(), name='billing-checkout'),
    path('billing/webhook', StripeWebhookView.as_view(), name='billing-webhook'),
    path('billing/mock-success', MockCheckoutSuccessView.as_view(), name='billing-mock-success'),
    
    path('', include(router.urls)),
]
