from aiogram.fsm.state import State, StatesGroup


class CoverLetterGeneration(StatesGroup):
    job_selected = State()
    customizing = State()
    generating = State()
    displayed = State()
    quota_exhausted = State()
