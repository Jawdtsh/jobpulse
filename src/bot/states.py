from aiogram.fsm.state import State, StatesGroup


class CVUploadState(StatesGroup):
    waiting_for_file = State()
    processing_file = State()
    confirming_replace = State()


class SettingsState(StatesGroup):
    threshold_editing = State()


class MyJobsState(StatesGroup):
    browsing = State()


class CoverLetterGeneration(StatesGroup):
    job_selected = State()
    customizing = State()
    generating = State()
    displayed = State()
    quota_exhausted = State()
