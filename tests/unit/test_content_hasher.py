from src.utils.content_hasher import compute_content_hash


class TestDeterministicOutput:
    def test_same_input_same_hash(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_hash_is_sha256_hex(self):
        h = compute_content_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestNormalizationBeforeHashing:
    def test_whitespace_insensitive(self):
        h1 = compute_content_hash("hello world")
        h2 = compute_content_hash("hello   world")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = compute_content_hash("Hello World")
        h2 = compute_content_hash("hello world")
        assert h1 == h2

    def test_url_stripped(self):
        h1 = compute_content_hash("job at http://example.com")
        h2 = compute_content_hash("job at https://other.com")
        assert h1 == h2

    def test_newlines_collapsed(self):
        h1 = compute_content_hash("hello\nworld")
        h2 = compute_content_hash("hello world")
        assert h1 == h2


class TestDifferentInputs:
    def test_different_inputs_different_hash(self):
        h1 = compute_content_hash("first post")
        h2 = compute_content_hash("second post")
        assert h1 != h2

    def test_empty_input(self):
        h = compute_content_hash("")
        assert len(h) == 64
