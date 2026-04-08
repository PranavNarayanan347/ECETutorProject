from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from services.api.schemas.request_response import (
    ChatRequest,
    ChatResponse,
    RetrievalTraceModel,
)
from services.retrieval.context_builder import ContextBuilder
from services.retrieval.hybrid_retriever import HybridRetriever
from services.retrieval.query_rewriter import QueryRewriter
from services.retrieval.reranker import Reranker
from services.storage.models import ChatTurn, Citation
from services.tutor_engine.groundedness_check import GroundednessChecker
from services.tutor_engine.llm_client import LLMClient
from services.tutor_engine.prompt_templates import PromptTemplates
from services.tutor_engine.socratic_policy import SocraticPolicyEngine

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    def __init__(self, session_manager, postgres_repo, vector_repo, keyword_repo) -> None:
        self.session_manager = session_manager
        self.postgres_repo = postgres_repo
        self.query_rewriter = QueryRewriter()
        self.hybrid_retriever = HybridRetriever(vector_repo, keyword_repo)
        self.reranker = Reranker()
        self.context_builder = ContextBuilder()
        self.policy = SocraticPolicyEngine()
        self.prompts = PromptTemplates()
        self.llm = LLMClient()
        self.groundedness = GroundednessChecker(llm_client=self.llm)

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        start = perf_counter()
        state = self.session_manager.get_state(request.session_id)

        rewrite = self.query_rewriter.rewrite(request.message)
        candidates = self.hybrid_retriever.retrieve(rewrite, top_k=20)
        selected = self.reranker.rerank(rewrite, candidates, top_k=6)
        context, citations, selected_ids = self.context_builder.build(selected)

        response_type = self.policy.choose_response_type(
            message=request.message,
            allow_full_solution=request.allow_full_solution,
            hint_level=state.hint_level,
        )

        if not candidates:
            content = (
                "I don't have enough source material on this topic yet. "
                "Could you rephrase your question, or let your instructor know "
                "this topic needs course material uploaded?"
            )
            confidence, next_action = 0.15, "clarify"
        elif self.llm.available:
            system_prompt = self.prompts.system_prompt(response_type)
            user_msg = self.prompts.user_message(request.message, context)
            try:
                content = self.llm.generate(system_prompt, user_msg)
            except Exception as exc:
                logger.warning("LLM generation failed (%s); using fallback.", exc)
                content = self.prompts.build_fallback(response_type, request.message, context)
            confidence, next_action = self.groundedness.check(content, context, citations)
        else:
            content = self.prompts.build_fallback(response_type, request.message, context)
            confidence, next_action = self.groundedness.check(content, context, citations)

        elapsed_ms = int((perf_counter() - start) * 1000)
        trace = RetrievalTraceModel(
            query=request.message,
            rewrite=rewrite,
            candidate_count=len(candidates),
            selected_chunk_ids=selected_ids,
            latency_ms=elapsed_ms,
        )

        turn_id = f"turn_{uuid4().hex[:12]}"
        self.postgres_repo.save_chat_turn(
            ChatTurn(
                turn_id=turn_id,
                session_id=request.session_id,
                role="assistant",
                content=content,
                response_type=response_type.value,
                confidence=confidence,
            )
        )
        self.postgres_repo.save_citations(
            Citation(
                citation_id=f"cit_{uuid4().hex[:12]}",
                turn_id=turn_id,
                chunk_id=c.chunk_id,
                doc_id=c.doc_id,
                page=c.page,
                snippet=c.snippet,
            )
            for c in citations
        )

        if response_type.value == "question":
            state.hint_level = 1
        elif response_type.value == "hint":
            state.hint_level += 1

        logger.info(
            "Chat %s | type=%s confidence=%.2f latency=%dms chunks=%d",
            request.session_id, response_type.value, confidence, elapsed_ms, len(selected_ids),
        )

        return ChatResponse(
            response_type=response_type,
            content=content,
            citations=citations,
            confidence=confidence,
            next_action=next_action,
            retrieval_trace=trace,
        )
