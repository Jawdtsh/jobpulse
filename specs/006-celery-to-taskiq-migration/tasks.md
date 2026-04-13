---

description: "Task list for Celery to TaskIQ migration"
---

# Tasks: Migrate from Celery to TaskIQ

**Input**: Design documents from `/specs/006-celery-to-taskiq-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Not required - FR-008 covers test updates as part of migration

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization - install new dependencies

- [x] T001 Update requirements.txt in requirements.txt - remove celery==5.4.0, add taskiq==0.11.7 and taskiq-redis==1.0.0
- [x] T002 Install new dependencies via pip in requirements.txt

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core TaskIQ infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create workers/taskiq_app.py with TaskIQ broker and scheduler configuration (Redis broker, result backend, event handlers)
- [x] T004 Delete workers/celery_app.py after TaskIQ is operational
- [x] T005 [P] Verify TaskIQ can connect to Redis via settings.redis.redis_url

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Migrate Task Queue Infrastructure (Priority: P1) 🎯 MVP

**Goal**: Replace Celery tasks with TaskIQ native async tasks - worker and scheduler operational

**Independent Test**: TaskIQ worker starts, connects to Redis, executes tasks. Scheduler registers periodic tasks.

### Implementation for User Story 1

- [x] T006 [P] [US1] Convert ingestion_tasks.py in workers/tasks/ingestion_tasks.py - Celery to TaskIQ native async
- [x] T007 [P] [US1] Convert matching_tasks.py in workers/tasks/matching_tasks.py - Celery to TaskIQ native async
- [x] T008 [US1] Register scheduled tasks with scheduler in workers/taskiq_app.py (every 3 min ingestion, every 1 min matching)
- [x] T009 [US1] Test TaskIQ worker starts and connects to Redis in workers/
- [x] T010 [US1] Test TaskIQ scheduler registers tasks in workers/

**Checkpoint**: At this point, User Story 1 should be fully functional

---

## Phase 4: User Story 2 - Update Service Layer Task Calls (Priority: P2)

**Goal**: Services use TaskIQ kiq() instead of Celery send_task

**Independent Test**: CV upload triggers ingestion pipeline via TaskIQ. New job stored triggers matching via TaskIQ.

### Implementation for User Story 2

- [x] T011 [P] [US2] Update cv_service.py in src/services/cv_service.py - replace send_task with kiq()
- [x] T012 [P] [US2] Update job_ingestion_service.py in src/services/job_ingestion_service.py - replace send_task with kiq()
- [x] T013 [US2] Test service layer task calls work correctly via src/ services/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work

---

## Phase 5: User Story 3 - Update Docker Infrastructure (Priority: P3)

**Goal**: docker-compose.yml updated to run TaskIQ workers

**Independent Test**: Docker containers start correctly with new commands

### Implementation for User Story 3

- [x] T014 [P] [US3] Update docker-compose.yml - replace celery-worker with taskiq-worker service
- [x] T015 [P] [US3] Update docker-compose.yml - replace celery-beat with taskiq-scheduler service
- [x] T016 [US3] Test docker-compose up starts containers correctly in docker-compose.yml

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T017 Run all existing tests to verify migration success in tests/
- [x] T018 Update constitution.md - change "Task Queue: Celery" to "Task Queue: TaskIQ"
- [x] T019 Verify quickstart.md scenarios pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories proceed in sequential priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 - uses TaskIQ tasks created in US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent Docker changes

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1 tasks T001, T002 can run in parallel
- Phase 2 tasks T003 can start after T002
- Phase 3 tasks T006, T007 (different files) can run in parallel
- Phase 5 tasks T014, T015 (different services) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch task conversions in parallel:
Task: "Convert ingestion_tasks.py in workers/tasks/ingestion_tasks.py"
Task: "Convert matching_tasks.py in workers/tasks/matching_tasks.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Polish phase → Final validation

### Sequential Team Strategy

1. Team completes Setup + Foundational together
2. Add User Story 1 → Test → Deploy/Demo
3. Add User Story 2 → Test → Deploy/Demo
4. Add User Story 3 → Test → Deploy/Demo
5. Polish

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a migration - changes are straightforward replacements

## Additional Implementation (Post-Migration Bug Fix)

- [x] T020 [P] Add find_similar_to_cv method in src/repositories/job_repository.py
- [x] T021 [P] Add match_cv_to_recent_jobs method in src/services/matching_service.py
- [x] T022 Add lazy initialization to src/workers/taskiq_app.py
- [x] T023 Update cv_tasks.py to use MatchingService instead of direct repo calls