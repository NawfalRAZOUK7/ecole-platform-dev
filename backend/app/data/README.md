# data/ — Static Reference Data

Static data files used by the application during runtime. Non-code assets that inform business logic.

## Directory Structure

```
data/
└── common_passwords.txt  # Password blacklist for policy enforcement
```

## common_passwords.txt — Password Blacklist

Contains commonly used or weak passwords that users should not use. Supports password policy validation.

### Purpose

- Enforce password strength
- Prevent commonly exploited passwords
- Improve security posture
- Meet compliance requirements

### File Format

One password per line, lowercase:

```
123456
password
12345678
qwerty
abc123
monkey
1234567
letmein
trustno1
dragon
baseball
111111
iloveyou
master
sunshine
ashley
bailey
passw0rd
shadow
123123
654321
superman
qazwsx
michael
football
...
```

### Size

~10,000 most common passwords (curated from public breach databases)

### Usage

Password validation service checks user input:

```python
class PasswordPolicyService:
    """Enforce password requirements."""

    def __init__(self):
        # Load blacklist at startup
        with open("app/data/common_passwords.txt") as f:
            self.blacklist = set(line.strip().lower() for line in f)

    def validate_password(self, password: str) -> bool:
        """Validate password strength."""

        # Length requirement
        if len(password) < 8:
            raise PasswordTooShortError("Min 8 characters")

        # Complexity requirement
        if not self._has_complexity(password):
            raise PasswordTooWeakError("Need uppercase, lowercase, number, symbol")

        # Not in blacklist
        if password.lower() in self.blacklist:
            raise PasswordCommonError("This password is too common")

        return True

    def _has_complexity(self, password: str) -> bool:
        """Check password has variety."""
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in "!@#$%^&*()" for c in password)

        return has_upper and has_lower and has_digit and has_symbol
```

### Integration

Called during registration and password change:

```python
# In auth.py service
async def register_user(
    self,
    email: str,
    password: str,
    ...
):
    # Validate password
    self.password_policy.validate_password(password)

    # Hash password
    password_hash = hash_password(password)

    # Create user
    user = User(email=email, password_hash=password_hash, ...)
    # ...
```

Also used in Pydantic validators:

```python
class UserRegisterRequest(BaseModel):
    """User registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        # Reuses PasswordPolicyService validation
        service = PasswordPolicyService()
        service.validate_password(v)
        return v
```

### Updating Blacklist

Update periodically from breach databases:

```bash
# Download HIBP Common Passwords list
curl https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt \
  > app/data/common_passwords.txt

# Sort and deduplicate
sort app/data/common_passwords.txt | uniq > temp.txt
mv temp.txt app/data/common_passwords.txt

# Commit update
git add app/data/common_passwords.txt
git commit -m "chore: update password blacklist"
```

### Performance

Loaded once at startup (fast lookup):

```python
# Startup
self.blacklist = set(...)  # O(n) load time
password in self.blacklist  # O(1) lookup time
```

For 10k passwords: ~50ms load, <1ms per check

## Other Static Data

### Future additions

- `city_codes.json` — Moroccan city mappings
- `currencies.json` — Supported currency rates
- `holiday_calendar.json` — Public holidays (Morocco)
- `grade_scales.json` — Grade conversion tables
- `school_types.json` — School category definitions

### Example: holiday_calendar.json

```json
{
  "2024": [
    {
      "date": "2024-01-01",
      "name": "New Year's Day",
      "country": "MA"
    },
    {
      "date": "2024-01-11",
      "name": "Independence Day",
      "country": "MA"
    },
    {
      "date": "2024-09-21",
      "name": "Youth Day",
      "country": "MA"
    },
    {
      "date": "2024-11-06",
      "name": "Green March",
      "country": "MA"
    },
    {
      "date": "2024-11-18",
      "name": "Independence Day",
      "country": "MA"
    }
  ]
}
```

Used in timetable generation and event creation:

```python
async def generate_timetable(self, academic_year_id: int):
    # Load holidays
    holidays = load_json("app/data/holiday_calendar.json")

    # Generate slots, skipping holidays
    for slot in slots:
        if slot.date not in holidays:
            save_slot(slot)
```

## Access from Code

Load static data:

```python
import json
from pathlib import Path

def load_static_data(filename: str) -> dict | list:
    """Load static data file."""
    path = Path("app/data") / filename
    with open(path) as f:
        return json.load(f)

# Usage
holidays = load_static_data("holiday_calendar.json")
cities = load_static_data("city_codes.json")
```

Or cache in memory:

```python
class StaticDataCache:
    """In-memory cache of static data."""

    _cache = {}

    @classmethod
    def load(cls, filename: str):
        if filename not in cls._cache:
            path = Path("app/data") / filename
            with open(path) as f:
                cls._cache[filename] = json.load(f)
        return cls._cache[filename]

# Usage (lazy loaded)
holidays = StaticDataCache.load("holiday_calendar.json")
```

## Next Steps

- See `services/` for usage examples
- See `core/password_policy.py` for password validation
- See `app/models/` for data that should be in database vs static files
