from typing import Optional, List
import uuid
from ragaas.application.interfaces.repositories import (
    ITenantRepository, IEndUserRepository, IChatSessionRepository, 
    INamespaceRepository, IDocumentRepository
)
from ragaas.domain.entities.tenant import Tenant as DomainTenant
from ragaas.domain.entities.end_user import EndUser as DomainEndUser
from ragaas.domain.entities.chat_session import ChatSession as DomainChatSession, ChatMessage as DomainChatMessage
from ragaas.domain.entities.namespace import Namespace as DomainNamespace
from ragaas.domain.entities.document import Document as DomainDocument

from ragaas.domain.value_objects import PlanTier, LLMConfig, EmbeddingConfig, Platform, MessageRole, SourceReference, DocumentStatus

from ragaas.models.core import Tenant as DjangoTenant, Namespace as DjangoNamespace, Document as DjangoDocument
from ragaas.models.chat import EndUser as DjangoEndUser, ChatSession as DjangoChatSession, ChatMessage as DjangoChatMessage

class DjangoTenantRepository(ITenantRepository):
    """Implementation of ITenantRepository using Django ORM."""
    def get_by_id(self, tenant_id: uuid.UUID) -> Optional[DomainTenant]:
        try:
            orm_obj = DjangoTenant.objects.get(id=tenant_id)
            return self._to_domain(orm_obj)
        except DjangoTenant.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> Optional[DomainTenant]:
        try:
            orm_obj = DjangoTenant.objects.get(email=email)
            return self._to_domain(orm_obj)
        except DjangoTenant.DoesNotExist:
            return None

    def save(self, tenant: DomainTenant) -> None:
        DjangoTenant.objects.update_or_create(
            id=tenant.id,
            defaults={
                'email': tenant.email,
                'name': tenant.name,
                'plan': tenant.plan.value,
                'status': tenant.status,
                'is_active': tenant.is_active,
                'llm_provider': tenant.llm_config.provider,
                'embedding_provider': tenant.embedding_config.provider,
            }
        )

    def _to_domain(self, orm_obj: DjangoTenant) -> DomainTenant:
        return DomainTenant(
            id=orm_obj.id, email=orm_obj.email, name=orm_obj.name,
            plan=PlanTier(orm_obj.plan), status=orm_obj.status, is_active=orm_obj.is_active,
            can_deploy_api=orm_obj.can_deploy_api, allowed_vector_dbs=orm_obj.allowed_vector_dbs,
            allowed_rag_types=orm_obj.allowed_rag_types,
            created_at=orm_obj.created_at, updated_at=orm_obj.updated_at,
            llm_config=LLMConfig(provider=orm_obj.llm_provider, model=orm_obj.llm_model),
            embedding_config=EmbeddingConfig(provider=orm_obj.embedding_provider, model=orm_obj.embedding_model)
        )

class DjangoEndUserRepository(IEndUserRepository):
    """Implementation of IEndUserRepository using Django ORM."""
    def get_by_id(self, end_user_id: uuid.UUID) -> Optional[DomainEndUser]:
        try:
            orm_obj = DjangoEndUser.objects.get(id=end_user_id)
            return self._to_domain(orm_obj)
        except DjangoEndUser.DoesNotExist:
            return None

    def get_by_external_id(self, tenant_id: uuid.UUID, external_id: str) -> Optional[DomainEndUser]:
        try:
            orm_obj = DjangoEndUser.objects.get(tenant_id=tenant_id, external_id=external_id)
            return self._to_domain(orm_obj)
        except DjangoEndUser.DoesNotExist:
            return None

    def save(self, end_user: DomainEndUser) -> None:
        DjangoEndUser.objects.update_or_create(
            id=end_user.id,
            defaults={
                'tenant_id': end_user.tenant_id,
                'external_id': end_user.external_id,
                'name': end_user.name,
                'platform': end_user.platform.value,
                'is_active': end_user.is_active,
                'metadata': end_user.metadata
            }
        )

    def _to_domain(self, orm_obj: DjangoEndUser) -> DomainEndUser:
        return DomainEndUser(
            id=orm_obj.id, tenant_id=orm_obj.tenant_id, external_id=orm_obj.external_id,
            name=orm_obj.name, platform=Platform(orm_obj.platform), is_active=orm_obj.is_active,
            metadata=orm_obj.metadata, created_at=orm_obj.created_at
        )

class DjangoChatSessionRepository(IChatSessionRepository):
    """Implementation of IChatSessionRepository using Django ORM."""
    def get_by_id(self, session_id: uuid.UUID) -> Optional[DomainChatSession]:
        try:
            orm_session = DjangoChatSession.objects.prefetch_related('messages').get(id=session_id)
            messages = [
                DomainChatMessage(
                    id=m.id, session_id=m.session_id, role=MessageRole(m.role), content=m.content,
                    created_at=m.created_at, tokens_used=m.tokens_used,
                    sources=[SourceReference(**s) for s in m.sources]
                ) for m in orm_session.messages.all()
            ]
            return DomainChatSession(
                id=orm_session.id, end_user_id=orm_session.end_user_id, namespace_id=orm_session.namespace_id,
                title=orm_session.title, created_at=orm_session.created_at, updated_at=orm_session.updated_at,
                messages=messages
            )
        except DjangoChatSession.DoesNotExist:
            return None

    def list_by_end_user(self, end_user_id: uuid.UUID) -> List[DomainChatSession]:
        # Implementation omitted for brevity
        return []

    def save(self, session: DomainChatSession) -> None:
        orm_session, _ = DjangoChatSession.objects.update_or_create(
            id=session.id,
            defaults={
                'end_user_id': session.end_user_id,
                'namespace_id': session.namespace_id,
                'title': session.title
            }
        )
        # Save messages
        for msg in session.messages:
            DjangoChatMessage.objects.update_or_create(
                id=msg.id,
                defaults={
                    'session_id': session.id,
                    'role': msg.role.value,
                    'content': msg.content,
                    'tokens_used': msg.tokens_used,
                    'sources': [s.__dict__ for s in msg.sources],
                    'created_at': msg.created_at
                }
            )

class DjangoNamespaceRepository(INamespaceRepository):
    # Mapping boilerplate...
    pass

class DjangoDocumentRepository(IDocumentRepository):
    # Mapping boilerplate...
    pass
