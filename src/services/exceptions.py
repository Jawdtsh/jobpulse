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


class CVFileSizeExceededError(Exception):
    def __init__(self, max_size_mb: int = 5, **context):
        self.max_size_mb = max_size_mb
        self.context = context
        self.message = f"CV file size exceeds maximum of {max_size_mb}MB"
        super().__init__(self.message)


class CVFormatNotSupportedError(Exception):
    def __init__(self, file_format: str = "", **context):
        self.file_format = file_format
        self.context = context
        self.message = f"CV file format not supported: {file_format}"
        super().__init__(self.message)


class CVTextExtractionError(Exception):
    def __init__(self, message: str = "Failed to extract text from CV", **context):
        self.message = message
        self.context = context
        super().__init__(self.message)


class CVQuotaExceededError(Exception):
    def __init__(self, message: str = "CV evaluation quota exceeded", **context):
        self.message = message
        self.context = context
        super().__init__(self.message)


class CVLimitExceededError(Exception):
    def __init__(
        self, message: str = "CV limit exceeded for your subscription tier", **context
    ):
        self.message = message
        self.context = context
        super().__init__(self.message)


class CVDeletedError(Exception):
    def __init__(self, message: str = "Cannot operate on deleted CV", **context):
        self.message = message
        self.context = context
        super().__init__(self.message)


class CVUploadInProgressError(Exception):
    def __init__(
        self, message: str = "Upload already in progress, please wait.", **context
    ):
        self.message = message
        self.context = context
        super().__init__(self.message)


class JobNotFoundError(Exception):
    def __init__(self, job_id: str = "", **context):
        self.job_id = job_id
        self.context = context
        self.message = f"Job not found: {job_id}"
        super().__init__(self.message)


class EmbeddingNotAvailableError(Exception):
    def __init__(self, entity_type: str = "", entity_id: str = "", **context):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.context = context
        self.message = f"Embedding not available for {entity_type}: {entity_id}"
        super().__init__(self.message)


class ProTierRequiredError(Exception):
    def __init__(
        self, message: str = "This feature requires Pro subscription", **context
    ):
        self.message = message
        self.context = context
        super().__init__(self.message)


class ThresholdOutOfRangeError(Exception):
    def __init__(self, value: float = 0.0, **context):
        self.value = value
        self.context = context
        self.message = f"Threshold {value} is outside valid range 0.60-1.00"
        super().__init__(self.message)


class InsufficientBalanceError(Exception):
    def __init__(self, message: str = "Insufficient wallet balance", **context):
        self.message = message
        self.context = context
        super().__init__(self.message)


class WalletError(Exception):
    def __init__(self, message: str = "Wallet operation failed", **context):
        self.message = message
        self.context = context
        super().__init__(self.message)
