from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from src.services.cv_parser import CVParser


@pytest.fixture
def parser():
    return CVParser()


class TestCVParser:
    @pytest.mark.asyncio
    async def test_extract_text_txt(self, parser):
        data = BytesIO(
            b"Hello, this is my CV with some content that is long enough to pass validation checks."
        )
        result = await parser.extract_text(data, "txt")
        assert "Hello" in result

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(self, parser):
        with pytest.raises(ValueError, match="Unsupported format"):
            await parser.extract_text(BytesIO(b"data"), "xlsx")

    @pytest.mark.asyncio
    async def test_extract_text_from_txt_file(self, parser):
        data = BytesIO(
            b"Python Developer CV content here with enough text to be valid."
        )
        result = await parser.extract_text_from_txt(data)
        assert "Python Developer" in result

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_primary_returns_empty_on_import_error(
        self, parser
    ):
        with patch.dict("sys.modules", {"pypdf": None}):
            result = await parser._extract_pdf_primary(BytesIO(b"fake"))
            assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_fallback_returns_empty_on_exception(
        self, parser
    ):
        with patch.dict("sys.modules", {"pdfplumber": None}):
            result = await parser._extract_pdf_fallback(BytesIO(b"fake"))
            assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_docx(self, parser):
        mock_doc = MagicMock()
        mock_doc.paragraphs = [
            MagicMock(text="John Doe"),
            MagicMock(text="Software Engineer"),
        ]
        with patch("docx.Document", return_value=mock_doc):
            result = await parser.extract_text_from_docx(BytesIO(b"fake"))
            assert "John Doe" in result
            assert "Software Engineer" in result

    @pytest.mark.asyncio
    async def test_extract_text_from_docx_import_error(self, parser):
        with patch.dict("sys.modules", {"docx": None}):
            result = await parser.extract_text_from_docx(BytesIO(b"fake"))
            assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_docx_exception_returns_empty(self, parser):
        with patch("docx.Document", side_effect=RuntimeError("parse error")):
            result = await parser.extract_text_from_docx(BytesIO(b"fake"))
            assert result == ""

    @pytest.mark.asyncio
    async def test_extract_text_from_pdf_with_pypdf_success(self, parser):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "CV content from PDF with enough text for validation."
        )
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pypdf = MagicMock()
        mock_pypdf.PdfReader = MagicMock(return_value=mock_reader)
        with patch.dict("sys.modules", {"pypdf": mock_pypdf}):
            result = await parser.extract_text_from_pdf(BytesIO(b"fake"))
            assert "CV content" in result
