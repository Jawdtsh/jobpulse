import asyncio
import logging
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

_MIN_TEXT_LENGTH = 100


class CVParser:
    async def extract_text(self, file_path: Path | BytesIO, fmt: str) -> str:
        fmt = fmt.lower().lstrip(".")
        if fmt == "pdf":
            return await self.extract_text_from_pdf(file_path)
        if fmt == "docx":
            return await self.extract_text_from_docx(file_path)
        if fmt == "txt":
            return await self.extract_text_from_txt(file_path)
        raise ValueError(f"Unsupported format: {fmt}")

    async def extract_text_from_pdf(self, file_path: Path | BytesIO) -> str:
        text = await self._extract_pdf_primary(file_path)
        if text and len(text.strip()) >= _MIN_TEXT_LENGTH:
            return text
        fallback = await self._extract_pdf_fallback(file_path)
        if fallback and len(fallback.strip()) >= _MIN_TEXT_LENGTH:
            return fallback
        return text or fallback or ""

    async def _extract_pdf_primary(self, file_path: Path | BytesIO) -> str:
        try:
            from pypdf import PdfReader

            def _read():
                reader = PdfReader(file_path)
                pages = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        pages.append(t)
                return "\n".join(pages)

            return await asyncio.to_thread(_read)
        except ImportError:
            return ""
        except Exception:
            logger.warning("pypdf extraction failed", exc_info=True)
            return ""

    async def _extract_pdf_fallback(self, file_path: Path | BytesIO) -> str:
        try:
            import pdfplumber

            def _read():
                pages = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            pages.append(t)
                return "\n".join(pages)

            return await asyncio.to_thread(_read)
        except Exception:
            logger.warning("pdfplumber extraction failed", exc_info=True)
            return ""

    async def extract_text_from_docx(self, file_path: Path | BytesIO) -> str:
        try:
            from docx import Document
        except ImportError:
            logger.warning("python-docx not installed, cannot extract DOCX")
            return ""

        def _read():
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text)

        try:
            return await asyncio.to_thread(_read)
        except Exception:
            logger.warning("DOCX extraction failed", exc_info=True)
            return ""

    async def extract_text_from_txt(self, file_path: Path | BytesIO) -> str:
        if isinstance(file_path, BytesIO):
            return file_path.read().decode("utf-8", errors="replace")
        return await asyncio.to_thread(
            file_path.read_text, encoding="utf-8", errors="replace"
        )
