class AIServiceUnavailableError(Exception):
    def __init__(self, message: str = "All AI providers are unavailable"):
        self.message = message
        super().__init__(self.message)


class DailyLimitReachedError(Exception):
    def __init__(self, model: str = "", message: str = ""):
        self.model = model
        self.message = message or f"Daily limit reached for model: {model}"
        super().__init__(self.message)


class InvalidModelTypeError(Exception):
    def __init__(self, model_type: str = ""):
        self.model_type = model_type
        self.message = f"Invalid model type: {model_type}"
        super().__init__(self.message)


class InvalidEmbeddingDimensionsError(Exception):
    def __init__(self, expected: int = 0, actual: int = 0):
        self.expected = expected
        self.actual = actual
        self.message = (
            f"Invalid embedding dimensions: expected {expected}, got {actual}"
        )
        super().__init__(self.message)


class PipelineError(Exception):
    def __init__(self, message: str = "Pipeline execution failed"):
        self.message = message
        super().__init__(self.message)


class SessionExhaustedError(Exception):
    def __init__(self, message: str = "All Telegram sessions are exhausted"):
        self.message = message
        super().__init__(self.message)


class ChannelInaccessibleError(Exception):
    def __init__(self, channel: str = "", message: str = ""):
        self.channel = channel
        self.message = message or f"Channel inaccessible: {channel}"
        super().__init__(self.message)
