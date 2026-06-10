import dataclasses
from rest_framework.exceptions import ValidationError
from phoenix.framework.rag.config import RAGConfig, CAGConfig, AgenticRAGConfig, MultiModalRAGConfig
from ragaas.models import Namespace

class NamespaceService:
    @staticmethod
    def create_namespace(tenant, data):
        rag_type = data.get('rag_type', 'standard')
        llm_model = data.get('llm_model', 'gpt-4o-mini')
        embedding_provider = data.get('embedding_provider', 'dashscope')
        
        plan_limits = {
            'free': {'rag': ['standard'], 'embed': ['sentence-transformers', 'dashscope', 'local']},
            'start': {'rag': ['standard', 'advanced'], 'embed': ['sentence-transformers', 'dashscope', 'local']},
            'mid': {'rag': ['standard', 'advanced', 'cag'], 'embed': ['sentence-transformers', 'dashscope', 'local', 'openai', 'cohere']},
            'prime': {'rag': ['standard', 'advanced', 'cag', 'agentic', 'multimodal'], 'embed': ['sentence-transformers', 'dashscope', 'local', 'openai', 'cohere', 'voyage']},
            'enterprise': {'rag': ['standard', 'advanced', 'cag', 'agentic', 'multimodal'], 'embed': ['sentence-transformers', 'dashscope', 'local', 'openai', 'cohere', 'voyage', 'custom']}
        }
        
        active_limits = plan_limits.get(tenant.plan, plan_limits['free'])
        allowed_rag = tenant.allowed_rag_types if tenant.allowed_rag_types else active_limits['rag']
        
        if rag_type not in allowed_rag:
            raise ValidationError(f"RAG type '{rag_type}' is not available on the {tenant.plan.title()} plan.")
            
        if embedding_provider not in active_limits['embed']:
            raise ValidationError(f"Embedding provider '{embedding_provider}' is not available on the {tenant.plan.title()} plan.")
        
        if rag_type == 'cag':
            phx_cfg = dataclasses.asdict(CAGConfig())
        elif rag_type == 'agentic':
            phx_cfg = dataclasses.asdict(AgenticRAGConfig())
        elif rag_type == 'multimodal':
            phx_cfg = dataclasses.asdict(MultiModalRAGConfig())
        else:
            phx_cfg = dataclasses.asdict(RAGConfig())
            
        provided_config = data.get('config', {})
        if isinstance(provided_config, dict):
            phx_cfg.update(provided_config)
            
        ns, created = Namespace.objects.get_or_create(
            tenant=tenant, 
            name=data.get('name'),
            defaults={
                'rag_type': rag_type,
                'config': phx_cfg,
                'llm_provider': data.get('llm_provider', 'openai'),
                'llm_model': data.get('llm_model', 'gpt-4o-mini'),
                'llm_api_key': data.get('llm_api_key'),
                'llm_base_url': data.get('llm_base_url'),
                'embedding_provider': data.get('embedding_provider', 'dashscope'),
                'embedding_model': data.get('embedding_model', 'text-embedding-v4'),
                'embedding_api_key': data.get('embedding_api_key'),
                'embedding_base_url': data.get('embedding_base_url'),
            }
        )
        return ns, created

    @staticmethod
    def delete_namespace(tenant, name):
        ns = Namespace.objects.filter(tenant=tenant, name=name).first()
        if ns:
            ns.delete()
            return True
        return False
