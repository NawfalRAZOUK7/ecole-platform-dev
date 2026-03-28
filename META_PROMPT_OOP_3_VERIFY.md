# Meta Prompt OOP-3: Verification

> Run this prompt AFTER all OOP refactor prompts have been executed.

---

You have completed the OOP refactoring of the Ecole Platform backend. Now verify everything.

## Verification Checks

Run each check and report PASS or FAIL.

### 1. File Structure
```bash
# Verify domain directory exists with all subdirectories
ls -la backend/app/domain/
ls -la backend/app/domain/value_objects/
ls -la backend/app/domain/events/
ls -la backend/app/domain/protocols/
```

### 2. Unit of Work
```bash
# Should return ZERO results (no direct commits in services)
grep -rn "db\.commit()" backend/app/services/ --include="*.py" | grep -v "uow" | grep -v "__pycache__"
grep -rn "db\.rollback()" backend/app/services/ --include="*.py" | grep -v "uow" | grep -v "__pycache__"

# Should find UnitOfWork imports in write services
grep -rn "from app.core.unit_of_work import" backend/app/services/ --include="*.py"
```

### 3. Value Objects
```bash
# Verify files exist
ls backend/app/domain/value_objects/grade.py
ls backend/app/domain/value_objects/money.py
ls backend/app/domain/value_objects/typed_id.py
ls backend/app/domain/value_objects/role_set.py

# Verify they validate correctly
python3 -c "
from app.domain.value_objects.grade import MoroccanGrade
from decimal import Decimal
# Should work
g = MoroccanGrade(Decimal('15'))
print(f'Grade: {g}, Mention: {g.mention}')
# Should raise ValueError
try:
    MoroccanGrade(Decimal('25'))
    print('FAIL: accepted grade > 20')
except ValueError:
    print('PASS: rejected grade > 20')
"
```

### 4. Profile System
```bash
# Verify models exist
grep -n "class AdminProfile" backend/app/models/iam.py
grep -n "class ContentManagerProfile" backend/app/models/iam.py

# Verify migration exists
ls backend/alembic/versions/*g26*

# Verify ProfileLoader exists
ls backend/app/services/profile_loader.py
ls backend/app/repositories/profile_loader.py
```

### 5. Domain Events
```bash
# Verify event files
ls backend/app/domain/events/base.py
ls backend/app/domain/events/lms.py
ls backend/app/domain/events/calendar.py
ls backend/app/domain/events/billing.py
ls backend/app/domain/events/documents.py
ls backend/app/domain/events/auth.py

# Verify events are frozen dataclasses
grep -c "frozen=True" backend/app/domain/events/*.py

# Verify dispatcher exists with event registry
ls backend/app/services/event_dispatcher.py
grep -c "EVENT_HANDLERS" backend/app/services/event_dispatcher.py
```

### 6. Delivery Strategies
```bash
ls backend/app/services/delivery/base.py
ls backend/app/services/delivery/push.py
ls backend/app/services/delivery/email_delivery.py
ls backend/app/services/delivery/sms_delivery.py
ls backend/app/services/delivery/in_app.py
```

### 7. Event Wiring
```bash
# Should find event emissions in services
grep -rn "dispatch(" backend/app/services/ --include="*.py" | grep -v "__pycache__" | grep -v "event_dispatcher"
```

### 8. Evaluatable Protocol
```bash
ls backend/app/domain/protocols/evaluatable.py
ls backend/app/domain/protocols/grading.py
ls backend/app/services/student_work.py
ls backend/app/schemas/student_work.py

# Verify student-work endpoint registered
grep -n "student.work\|student_work" backend/app/api/v1/router.py
```

### 9. LMS Split
```bash
# Verify directory exists
ls backend/app/services/lms/

# Verify sub-services exist
ls backend/app/services/lms/course_service.py
ls backend/app/services/lms/assignment_service.py
ls backend/app/services/lms/quiz_service.py
ls backend/app/services/lms/content_service.py
ls backend/app/services/lms/progress_service.py
ls backend/app/services/lms/__init__.py

# Verify original lms.py is gone
test -f backend/app/services/lms.py && echo "FAIL: lms.py still exists" || echo "PASS: lms.py replaced by directory"

# Verify each sub-service is under 500 lines
wc -l backend/app/services/lms/*.py
```

### 10. Import Health
```bash
cd backend && python3 -c "
from app.core.unit_of_work import UnitOfWork
from app.domain.value_objects.grade import MoroccanGrade
from app.domain.value_objects.money import Money
from app.domain.value_objects.role_set import RoleSet
from app.domain.events.base import DomainEvent
from app.domain.events.lms import GradePublished
from app.domain.protocols.evaluatable import Evaluatable
from app.domain.protocols.grading import GradingStrategy
from app.services.event_dispatcher import EventDispatcher
from app.services.profile_loader import ProfileLoader
from app.services.student_work import StudentWorkService
from app.services.lms import CourseService, AssignmentService, QuizService
print('ALL IMPORTS OK')
"
```

## Output Format

| # | Check | Status | Details |
|---|-------|--------|---------|
| 1 | File Structure | PASS/FAIL | ... |
| 2 | Unit of Work | PASS/FAIL | ... |
| 3 | Value Objects | PASS/FAIL | ... |
| 4 | Profile System | PASS/FAIL | ... |
| 5 | Domain Events | PASS/FAIL | ... |
| 6 | Delivery Strategies | PASS/FAIL | ... |
| 7 | Event Wiring | PASS/FAIL | ... |
| 8 | Evaluatable Protocol | PASS/FAIL | ... |
| 9 | LMS Split | PASS/FAIL | ... |
| 10 | Import Health | PASS/FAIL | ... |

---

CRITICAL RULE: NEVER run any git command. No git add, commit, push, stash, checkout. The user handles all git operations manually.
