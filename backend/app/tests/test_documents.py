"""Tests for document management."""
import pytest
from io import BytesIO
from uuid import uuid4
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db import Document, Tenant, User
from app.services.document_service import DocumentChunker, EmbeddingGenerator
from app.utils.security import hash_password


class TestDocumentChunker:
    """Test document chunking."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        chunker = DocumentChunker(chunk_size=10, overlap=2)

        text = " ".join([f"word{i}" for i in range(20)])
        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1
        assert all(chunk.strip() for chunk in chunks)

    def test_chunk_text_with_overlap(self):
        """Test that chunks have overlap."""
        chunker = DocumentChunker(chunk_size=10, overlap=3)

        text = " ".join([f"word{i}" for i in range(30)])
        chunks = chunker.chunk_text(text)

        # Check that consecutive chunks have overlapping words
        if len(chunks) > 1:
            chunk1_words = chunks[0].split()
            chunk2_words = chunks[1].split()

            # Some words should be in both chunks (overlap)
            overlap_words = set(chunk1_words) & set(chunk2_words)
            assert len(overlap_words) > 0

    def test_chunk_empty_text(self):
        """Test chunking empty text."""
        chunker = DocumentChunker()
        chunks = chunker.chunk_text("")
        assert len(chunks) == 0

    def test_chunk_short_text(self):
        """Test chunking text shorter than chunk size."""
        chunker = DocumentChunker(chunk_size=100)
        text = "This is a short text."
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1
        assert text.strip() in chunks[0]


class TestEmbeddingGenerator:
    """Test embedding generation."""

    def test_embed_text(self):
        """Test embedding generation."""
        try:
            generator = EmbeddingGenerator()
            embedding = generator.embed("This is a test sentence.")

            # Check embedding is a list of floats
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, float) for x in embedding)
            assert len(embedding) == 384  # all-MiniLM-L6-v2 output dimension

        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embed_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        try:
            generator = EmbeddingGenerator()

            text1 = "The cat sat on the mat."
            text2 = "The dog ran in the park."

            embedding1 = generator.embed(text1)
            embedding2 = generator.embed(text2)

            # Embeddings should be different
            assert embedding1 != embedding2

        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embed_similar_texts_similar_embeddings(self):
        """Test that similar texts produce similar embeddings."""
        try:
            from numpy import dot
            from numpy.linalg import norm

            generator = EmbeddingGenerator()

            text1 = "The cat is sleeping on the couch."
            text2 = "The cat is resting on the sofa."
            text3 = "The car is parked in the garage."

            embedding1 = generator.embed(text1)
            embedding2 = generator.embed(text2)
            embedding3 = generator.embed(text3)

            # Calculate cosine similarity
            def cosine_similarity(a, b):
                return dot(a, b) / (norm(a) * norm(b))

            sim_1_2 = cosine_similarity(embedding1, embedding2)
            sim_1_3 = cosine_similarity(embedding1, embedding3)

            # Texts 1 and 2 should be more similar than 1 and 3
            assert sim_1_2 > sim_1_3

        except ImportError:
            pytest.skip("sentence-transformers not installed")


class TestDocumentDatabase:
    """Test document database operations."""

    @pytest.mark.asyncio
    async def test_create_document(self, test_db, tenant_a, user_a):
        """Test creating a document in the database."""
        document = Document(
            tenant_id=tenant_a.id,
            original_filename="test.pdf",
            storage_path="/test/test.pdf",
            document_size_bytes=1000,
            uploaded_by=user_a.id,
            processed=False,
            metadata={"file_type": "pdf"},
        )

        test_db.add(document)
        await test_db.commit()
        await test_db.refresh(document)

        assert document.id is not None
        assert document.tenant_id == tenant_a.id
        assert document.original_filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_document_isolation(self, test_db, tenant_a, tenant_b, user_a, user_b):
        """Test that documents are isolated by tenant."""
        # Create document for tenant A
        doc_a = Document(
            tenant_id=tenant_a.id,
            original_filename="doc_a.pdf",
            storage_path="/a/doc_a.pdf",
            document_size_bytes=1000,
            uploaded_by=user_a.id,
            processed=False,
        )
        test_db.add(doc_a)
        await test_db.commit()

        # Switch to tenant B context and try to query
        from app.database.rls import set_tenant_context

        await set_tenant_context(test_db, str(tenant_b.id))

        result = await test_db.execute(
            select(Document).where(Document.id == doc_a.id)
        )
        doc = result.scalar_one_or_none()

        # Should not be visible to tenant B
        assert doc is None

    @pytest.mark.asyncio
    async def test_document_list_by_tenant(self, test_db, tenant_a, user_a):
        """Test listing documents for a tenant."""
        # Create multiple documents
        for i in range(3):
            doc = Document(
                tenant_id=tenant_a.id,
                original_filename=f"doc{i}.pdf",
                storage_path=f"/a/doc{i}.pdf",
                document_size_bytes=1000,
                uploaded_by=user_a.id,
                processed=False,
            )
            test_db.add(doc)

        await test_db.commit()

        # Query documents
        result = await test_db.execute(
            select(Document).where(Document.tenant_id == tenant_a.id)
        )
        documents = result.scalars().all()

        assert len(documents) == 3
        assert all(doc.tenant_id == tenant_a.id for doc in documents)


class TestFileExtraction:
    """Test text extraction from files."""

    def test_extract_txt(self, tmp_path):
        """Test extracting text from TXT file."""
        from app.services.document_service import DocumentService

        service = DocumentService()

        # Create test TXT file
        content = "Hello World\nThis is a test."
        file_path = tmp_path / "test.txt"
        file_path.write_text(content)

        extracted = service._extract_text(file_path)
        assert extracted == content

    def test_extract_pdf(self, tmp_path):
        """Test extracting text from PDF file."""
        try:
            from app.services.document_service import DocumentService
            import PyPDF2

            service = DocumentService()

            # Create a simple PDF
            file_path = tmp_path / "test.pdf"
            from io import BytesIO

            pdf_bytes = BytesIO()
            pdf_writer = PyPDF2.PdfWriter()

            # Add a blank page with text
            from reportlab.pdfgen import canvas

            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            c.drawString(100, 750, "Test PDF Content")
            c.save()
            buffer.seek(0)

            # Save to file
            file_path.write_bytes(buffer.getvalue())

            # Extract text
            extracted = service._extract_text(file_path)
            assert extracted.strip() != ""  # Should extract something

        except ImportError:
            pytest.skip("PDF libraries not installed")

    def test_extract_unsupported_file(self, tmp_path):
        """Test that unsupported file types raise error."""
        from app.services.document_service import DocumentService

        service = DocumentService()

        # Create unsupported file type
        file_path = tmp_path / "test.xyz"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="Unsupported file type"):
            service._extract_text(file_path)

    def test_extract_nonexistent_file(self):
        """Test that nonexistent files raise error."""
        from app.services.document_service import DocumentService

        service = DocumentService()

        with pytest.raises(FileNotFoundError):
            service._extract_text(Path("/nonexistent/file.txt"))
