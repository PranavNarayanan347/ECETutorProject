from __future__ import annotations

import hashlib
from uuid import uuid4

from fastapi import UploadFile

from services.api.schemas.request_response import IngestResponse
from services.ingestion.chunker import Chunker
from services.ingestion.embedder import Embedder
from services.ingestion.indexer import Indexer
from services.ingestion.pdf_parser import PDFParser
from services.storage.models import Chunk, Document


class IngestionRunner:
    def __init__(self, postgres_repo, vector_repo, keyword_repo, object_store) -> None:
        self.postgres_repo = postgres_repo
        self.object_store = object_store
        self.parser = PDFParser()
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.indexer = Indexer(postgres_repo, vector_repo, keyword_repo)

    async def run(
        self,
        course_id: str,
        title: str,
        file: UploadFile,
        module: str | None = None,
        topic: str | None = None,
    ) -> IngestResponse:
        raw = await file.read()
        digest = hashlib.sha256(raw).hexdigest()[:16]
        doc_id = f"doc_{digest}"

        if self.postgres_repo.get_document(doc_id):
            return IngestResponse(
                document_id=doc_id,
                status="complete",
                chunk_count=0,
                warnings=["Duplicate document detected; existing record reused."],
            )

        uri = self.object_store.put(doc_id, raw)
        document = Document(doc_id=doc_id, course_id=course_id, title=title, source_uri=uri)
        self.postgres_repo.upsert_document(document)

        pages = self.parser.parse(raw)
        warnings: list[str] = []
        if not pages or not any(page["text"].strip() for page in pages):
            warnings.append("No readable text detected.")

        chunk_specs = self.chunker.chunk_pages(pages)
        chunks: list[Chunk] = []
        for spec in chunk_specs:
            chunk_id = f"chk_{uuid4().hex[:12]}"
            text = spec["text"]
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    page=spec["page"],
                    section=spec["section"],
                    text=text,
                    token_count=spec["token_count"],
                    equation_flag=spec["equation_flag"],
                    embedding=self.embedder.embed(text),
                )
            )

        self.indexer.index_chunks(chunks)
        return IngestResponse(
            document_id=doc_id,
            status="complete",
            chunk_count=len(chunks),
            warnings=warnings,
        )
