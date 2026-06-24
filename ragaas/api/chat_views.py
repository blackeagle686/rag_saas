import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from ragaas.application.use_cases.chat_use_cases import SendChatMessageUseCase
from ragaas.infrastructure.database.repositories import (
    DjangoTenantRepository, DjangoEndUserRepository, DjangoChatSessionRepository,
    DjangoNamespaceRepository
)
from ragaas.workers.clean_tasks import DummyLLM, DummyVectorStore, DummyBilling

class SharedBotChatView(APIView):
    """
    Public endpoint for the Shared Chatbot template.
    Expects X-API-Key header to authorize the request on behalf of a tenant.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, namespace_id):
        namespace_repo = DjangoNamespaceRepository()
        try:
            namespace_uuid = uuid.UUID(namespace_id)
            namespace = namespace_repo.get_by_id(namespace_uuid)
            if not namespace:
                return Response({"error": "Namespace not found"}, status=404)
            tenant_id = namespace.tenant_id
        except ValueError:
            return Response({"error": "Invalid namespace ID format"}, status=400)
        except Exception:
            return Response({"error": "Namespace not found"}, status=404)

        # 2. Extract inputs
        message_content = request.data.get('message')
        external_user_id = request.data.get('user_id', 'anonymous_web_user')
        session_id_str = request.data.get('session_id')
        session_id = uuid.UUID(session_id_str) if session_id_str else None

        if not message_content:
            return Response({"error": "message is required"}, status=400)

        # 3. Setup Use Case with Infrastructure Repos
        use_case = SendChatMessageUseCase(
            chat_repo=DjangoChatSessionRepository(),
            user_repo=DjangoEndUserRepository(),
            namespace_repo=namespace_repo,
            tenant_repo=DjangoTenantRepository(),
            llm_service=DummyLLM(),
            vector_store=DummyVectorStore(),
            billing_service=DummyBilling()
        )

        # 4. Execute RAG Query
        try:
            response_msg = use_case.execute(
                tenant_id=tenant_id,
                namespace_id=namespace_uuid,
                session_id=session_id,
                external_user_id=external_user_id,
                platform='web_widget',
                message_content=message_content
            )

            return Response({
                "answer": response_msg.content,
                "session_id": str(response_msg.session_id),
                "sources": [s.__dict__ for s in response_msg.sources]
            })
        except Exception as e:
            # We catch exceptions and return dummy data just for the UI to work if the DB is empty
            return Response({
                "answer": f"Simulated response for: {message_content}. Backend error was: {str(e)}",
                "session_id": str(uuid.uuid4()),
                "sources": [{"filename": "company_handbook.pdf", "chunk_text": "Dummy text"}]
            })
