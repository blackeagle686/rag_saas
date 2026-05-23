"""
RAG query endpoint.

Accepts a natural language query, retrieves relevant
document chunks, and generates an answer using an LLM.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.middleware.rate_limiter import check_rate_limit
from api.schemas.query import QueryRequest, QueryResponse
from api.services.query_service import QueryService
from db.engine import get_db_session
from db.models.tenant import Tenant

router = APIRouter(prefix="/v1", tags=["Query"])


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query your documents",
    description=(
        "Ask a question against your indexed documents. "
        "The system retrieves relevant chunks from the specified namespace, "
        "builds a context, and uses an LLM to generate a grounded answer. "
        "Each response includes source references with similarity scores."
    ),
    responses={
        200: {
            "description": "Query answered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "According to your refund policy...",
                        "sources": [
                            {
                                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                                "filename": "refund-policy.pdf",
                                "chunk": "Customers may request refunds within 30 days...",
                                "score": 0.94,
                            }
                        ],
                        "latency_ms": 380,
                        "tokens_used": 1240,
                    }
                }
            },
        },
    },
)
async def query_documents(
    request: QueryRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> QueryResponse:
    service = QueryService(db)
    return await service.query(tenant, request)
