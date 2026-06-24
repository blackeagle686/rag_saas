import uuid
from datetime import datetime
from typing import Optional
from ragaas.domain.entities.chat_session import ChatSession, ChatMessage
from ragaas.domain.entities.end_user import EndUser
from ragaas.domain.value_objects import MessageRole, Platform, EventType
from ragaas.domain.exceptions import AuthenticationException, ResourceNotFoundException, QuotaExceededException
from ragaas.application.interfaces.repositories import IChatSessionRepository, IEndUserRepository, INamespaceRepository, ITenantRepository
from ragaas.application.interfaces.services import ILLMService, IVectorStore, IBillingService

class SendChatMessageUseCase:
    """Handles an end-user asking a question via a Chat Interface."""
    def __init__(
        self,
        chat_repo: IChatSessionRepository,
        user_repo: IEndUserRepository,
        namespace_repo: INamespaceRepository,
        tenant_repo: ITenantRepository,
        llm_service: ILLMService,
        vector_store: IVectorStore,
        billing_service: IBillingService
    ):
        self.chat_repo = chat_repo
        self.user_repo = user_repo
        self.namespace_repo = namespace_repo
        self.tenant_repo = tenant_repo
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.billing_service = billing_service

    def execute(self, tenant_id: uuid.UUID, namespace_id: uuid.UUID, session_id: Optional[uuid.UUID], external_user_id: str, platform: str, message_content: str) -> ChatMessage:
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant or not tenant.can_query():
            raise QuotaExceededException("Tenant is inactive or suspended.")

        namespace = self.namespace_repo.get_by_id(namespace_id)
        if not namespace:
            raise ResourceNotFoundException("Namespace not found.")

        # Resolve End User
        user = self.user_repo.get_by_external_id(tenant_id, external_user_id)
        if not user:
            user = EndUser(id=uuid.uuid4(), tenant_id=tenant_id, platform=Platform(platform), created_at=datetime.utcnow(), external_id=external_user_id)
            self.user_repo.save(user)
        
        if not user.is_active:
            raise AuthenticationException("End User access revoked.")

        # Resolve or Create Session
        if session_id:
            session = self.chat_repo.get_by_id(session_id)
            if not session:
                raise ResourceNotFoundException("Session not found.")
        else:
            session = ChatSession(id=uuid.uuid4(), end_user_id=user.id, namespace_id=namespace.id, title="New Chat", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
            self.chat_repo.save(session)

        # Execute RAG Logic
        query_embedding = self.llm_service.generate_embedding(message_content, namespace.embedding_config)
        sources = self.vector_store.search_similar(namespace.id, query_embedding, top_k=5)
        
        context_text = "\\n\\n".join([f"Source: {s.filename}\\n{s.chunk_text}" for s in sources])
        history_dicts = [{"role": m.role.value, "content": m.content} for m in session.get_conversation_history(limit=6)]
        
        response = self.llm_service.generate_answer(message_content, context_text, history_dicts, namespace.llm_config)

        # Save Messages
        now = datetime.utcnow()
        user_message = ChatMessage(id=uuid.uuid4(), session_id=session.id, role=MessageRole.USER, content=message_content, created_at=now)
        assistant_message = ChatMessage(id=uuid.uuid4(), session_id=session.id, role=MessageRole.ASSISTANT, content=response.answer, created_at=now, tokens_used=response.tokens_used.total_tokens, sources=sources)
        
        session.add_message(user_message)
        session.add_message(assistant_message)
        self.chat_repo.save(session)
        
        # Report Billing
        self.billing_service.report_usage(tenant_id, response.tokens_used.total_tokens, EventType.QUERY)
        
        return assistant_message
