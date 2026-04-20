from src.bot.states import (
    CVUploadState,
    SettingsState,
    MyJobsState,
    CoverLetterGeneration,
)


def test_cv_upload_state_has_required_states():
    assert hasattr(CVUploadState, "waiting_for_file")
    assert hasattr(CVUploadState, "processing_file")
    assert hasattr(CVUploadState, "confirming_replace")


def test_settings_state_has_threshold_editing():
    assert hasattr(SettingsState, "threshold_editing")


def test_my_jobs_state_has_browsing():
    assert hasattr(MyJobsState, "browsing")


def test_cover_letter_generation_states_intact():
    assert hasattr(CoverLetterGeneration, "customizing")
    assert hasattr(CoverLetterGeneration, "generating")
    assert hasattr(CoverLetterGeneration, "displayed")
