import src.repositories


def test_all_exports_correct_names():
    assert "ArchivedJobRepository" in src.repositories.__all__
    assert "ArchivedJob" not in src.repositories.__all__


def test_all_exports_importable():
    for name in src.repositories.__all__:
        assert hasattr(src.repositories, name), f"{name} not found in src.repositories"
