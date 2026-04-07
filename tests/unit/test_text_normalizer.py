from src.utils.text_normalizer import normalize_text


class TestLowercaseConversion:
    def test_converts_to_lowercase(self):
        assert normalize_text("Hello WORLD") == "hello world"

    def test_preserves_already_lowercase(self):
        assert normalize_text("hello") == "hello"


class TestWhitespaceCollapsing:
    def test_collapses_multiple_spaces(self):
        assert normalize_text("hello   world") == "hello world"

    def test_collapses_newlines(self):
        assert normalize_text("hello\n\nworld") == "hello world"

    def test_collapses_tabs(self):
        assert normalize_text("hello\tworld") == "hello world"

    def test_collapses_mixed_whitespace(self):
        assert normalize_text("hello \n\t  world") == "hello world"


class TestZeroWidthCharacterRemoval:
    def test_removes_zero_width_space(self):
        text = "hello\u200bworld"
        assert normalize_text(text) == "helloworld"

    def test_removes_zero_width_joiner(self):
        text = "hello\u200dworld"
        assert normalize_text(text) == "helloworld"

    def test_removes_bom(self):
        text = "\ufeffhello"
        assert normalize_text(text) == "hello"


class TestUnicodeFormattingRemoval:
    def test_removes_left_to_right_mark(self):
        text = "hello\u200eworld"
        assert normalize_text(text) == "helloworld"


class TestEmptyStringHandling:
    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_whitespace_only(self):
        assert normalize_text("   \n\t  ") == ""

    def test_normalize_none_returns_empty_string(self):
        assert normalize_text(None) == ""


class TestUrlRemoval:
    def test_removes_http_urls(self):
        assert normalize_text("check http://example.com here") == "check here"

    def test_removes_https_urls(self):
        assert normalize_text("visit https://example.com/path now") == "visit now"

    def test_removes_multiple_urls(self):
        assert normalize_text("a http://a.com b https://b.com c") == "a b c"


class TestStripping:
    def test_strips_leading_trailing(self):
        assert normalize_text("  hello  ") == "hello"


class TestNormalizationOrder:
    def test_normalize_order_is_stable(self):
        assert normalize_text(" hello world ") == "hello world"
        assert normalize_text("HELLO WORLD") == "hello world"
