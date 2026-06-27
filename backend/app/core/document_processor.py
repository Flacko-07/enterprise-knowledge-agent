"""
Document processing pipeline: loading, text extraction, chunking, metadata management.

Design Decisions:
- RecursiveCharacterTextSplitter: preserves semantic boundaries
  (paragraphs > sentences > words)
- Overlap: ensures context isn't lost at chunk boundaries
- Metadata propagation: every chunk carries document-level and
  chunk-level metadata for source citation
- Multi-format support: PDF, DOCX, TXT, MD
"""
import os
import uuid
import logging
from pathlib import Path
from dataclasses import dataclass, field

from pypdf import PdfReader
from docx import Document as DocxDocument

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class Chunk:
    """Processed text chunk with full metadata."""
    id: str
    text: str
    document: str
    page: int | None
    section: str | None
    chunk_index: int
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "metadata": {
                "document": self.document,
                "page": self.page,
                "section": self.section,
                "chunk_index": self.chunk_index,
                **self.metadata,
            },
        }


class DocumentProcessor:
    """Handles document loading, text extraction, and intelligent chunking."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    # ── Document Loading ───────────────────────────────────────────────

    def load_document(self, file_path: str) -> list[dict]:
        path = Path(file_path)
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        if path.suffix.lower() == ".pdf":
            return self._load_pdf(path)
        elif path.suffix.lower() == ".docx":
            return self._load_docx(path)
        else:
            return self._load_text(path)

    def _load_pdf(self, path: Path) -> list[dict]:
        pages = []
        try:
            reader = PdfReader(str(path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({
                        "text": text.strip(),
                        "page": i + 1,
                        "document": path.name,
                        "section": self._detect_section(text),
                    })
        except Exception as e:
            logger.error(f"Error loading PDF {path}: {e}")
            raise
        return pages

    def _load_docx(self, path: Path) -> list[dict]:
        doc = DocxDocument(str(path))
        pages = []
        current_section = "Introduction"
        current_text = []

        for para in doc.paragraphs:
            if para.style.name.startswith("Heading"):
                if current_text:
                    combined = "\n".join(current_text).strip()
                    if combined:
                        pages.append({
                            "text": combined,
                            "page": None,
                            "document": path.name,
                            "section": current_section,
                        })
                    current_text = []
                current_section = para.text.strip()
            else:
                current_text.append(para.text)

        if current_text:
            combined = "\n".join(current_text).strip()
            if combined:
                pages.append({
                    "text": combined,
                    "page": None,
                    "document": path.name,
                    "section": current_section,
                })
        return pages

    def _load_text(self, path: Path) -> list[dict]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                text = f.read().strip()

        return [{
            "text": text,
            "page": None,
            "document": path.name,
            "section": self._detect_section(text[:200]),
        }]

    # ── Chunking ───────────────────────────────────────────────────────

    def chunk_pages(self, pages: list[dict]) -> list[Chunk]:
        all_chunks = []
        chunk_index = 0

        for page_data in pages:
            text = page_data["text"]
            if len(text) <= self.chunk_size:
                all_chunks.append(Chunk(
                    id=str(uuid.uuid4()),
                    text=text,
                    document=page_data["document"],
                    page=page_data.get("page"),
                    section=page_data.get("section"),
                    chunk_index=chunk_index,
                ))
                chunk_index += 1
            else:
                chunks_text = self._recursive_split(text)
                for chunk_text in chunks_text:
                    if chunk_text.strip():
                        all_chunks.append(Chunk(
                            id=str(uuid.uuid4()),
                            text=chunk_text.strip(),
                            document=page_data["document"],
                            page=page_data.get("page"),
                            section=page_data.get("section"),
                            chunk_index=chunk_index,
                        ))
                        chunk_index += 1

        return all_chunks

    def _recursive_split(
        self, text: str, separators: list[str] = None,
    ) -> list[str]:
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]

        if len(text) <= self.chunk_size:
            return [text]

        for i, sep in enumerate(separators):
            if sep == "":
                return self._hard_split(text)

            parts = text.split(sep)
            if len(parts) == 1:
                continue

            chunks = []
            current_chunk = ""

            for part in parts:
                candidate = f"{current_chunk}{sep}{part}" if current_chunk else part
                if len(candidate) <= self.chunk_size:
                    current_chunk = candidate
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    if len(part) > self.chunk_size:
                        sub_chunks = self._recursive_split(part, separators[i + 1:])
                        chunks.extend(sub_chunks)
                        current_chunk = ""
                    else:
                        current_chunk = part

            if current_chunk:
                chunks.append(current_chunk)

            if self.chunk_overlap > 0 and len(chunks) > 1:
                overlapped = []
                for j, chunk in enumerate(chunks):
                    if j > 0:
                        overlap_text = chunks[j - 1][-self.chunk_overlap:]
                        chunk = f"{overlap_text} {chunk}"
                    overlapped.append(chunk)
                return overlapped

            return chunks

        return self._hard_split(text)

    def _hard_split(self, text: str) -> list[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _detect_section(text: str) -> str:
        lines = text.strip().split("\n")
        for line in lines[:3]:
            line = line.strip()
            if line and (line.isupper() or line.endswith(":")):
                return line.rstrip(":").strip().title()
        return "General"

    def process_document(self, file_path: str) -> list[Chunk]:
        pages = self.load_document(file_path)
        chunks = self.chunk_pages(pages)
        logger.info(f"Processed {file_path}: {len(pages)} pages → {len(chunks)} chunks")
        return chunks

    def process_directory(self, dir_path: str) -> list[Chunk]:
        all_chunks = []
        dir_path = Path(dir_path)

        if not dir_path.exists():
            logger.warning(f"Directory not found: {dir_path}")
            return all_chunks

        for file_path in dir_path.rglob("*"):
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    chunks = self.process_document(str(file_path))
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")

        logger.info(f"Directory processed: {len(all_chunks)} total chunks from {dir_path}")
        return all_chunks
