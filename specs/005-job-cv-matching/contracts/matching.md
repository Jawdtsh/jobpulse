# Matching Service Contracts

## Matching Service Interface

### match_job(job_id: UUID) → List[JobMatch]

Matches a job against all active CVs.

**Parameters**:
- `job_id`: UUID of the job to match

**Returns**: List of JobMatch records created

**Raises**:
- `JobNotFoundError`: If job doesn't exist
- `EmbeddingNotAvailableError`: If job has no embedding

### match_historical(user_id: UUID, days: int, resend_existing: bool) → List[JobMatch]

Matches a user's CVs against historical jobs.

**Parameters**:
- `user_id`: UUID of the user
- `days`: Number of days to look back (1-7)
- `resend_existing`: Whether to include already-matched jobs

**Returns**: List of JobMatch records created

**Raises**:
- `UserNotFoundError`: If user doesn't exist
- `InvalidDaysError`: If days < 1 or > 7
- `ProTierRequiredError`: If user is not Pro tier

## Notification Service Interface

### queue_notification(match: JobMatch, tier: SubscriptionTier)

Queues a notification for delivery.

**Parameters**:
- `match`: JobMatch record
- `tier`: SubscriptionTier (free, basic, pro)

### process_due_notifications()

Processes all notifications due for delivery.

**Returns**: Count of notifications sent

## Threshold Service Interface

### get_effective_threshold(user_id: UUID, job_category: str) → float

Gets the effective similarity threshold for a user/job combination.

**Parameters**:
- `user_id`: UUID of the user
- `job_category`: Category name (e.g., "Backend")

**Returns**: Effective threshold (0.00-1.00)

**Priority**: user preference > job category default > system default (0.80)

### set_user_threshold(user_id: UUID, threshold: float)

Sets a user's personal similarity threshold.

**Parameters**:
- `user_id`: UUID of the user
- `threshold`: Threshold value (0.60-1.00)

**Raises**:
- `ThresholdOutOfRangeError`: If threshold < 0.60 or > 1.00

## Repository Interface

### JobMatchRepository

```python
async def create(match: JobMatch) -> JobMatch
async def get_by_job(job_id: UUID) -> List[JobMatch]
async def get_by_user(user_id: UUID) -> List[JobMatch]
async def mark_notified(match_id: UUID) -> None
async def mark_clicked(match_id: UUID) -> None
async def delete_by_cv(cv_id: UUID) -> int  # Returns count deleted
```

### UserPreferencesRepository

```python
async def get_by_user(user_id: UUID) -> Optional[UserPreferences]
async def upsert(preferences: UserPreferences) -> UserPreferences
```