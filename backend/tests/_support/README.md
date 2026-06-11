# `tests/_support/` — shared test-support package

Reusable, framework-level helpers that keep individual tests short and
consistent. Four sub-packages:

| Package | What it holds | Import from |
|---|---|---|
| `builders/` | Fluent builders for test data (no DB) | `tests._support.builders` |
| `factories/` | Single import surface for `factory_boy` factories (+ onboarding) | `tests._support.factories` |
| `fixtures/` | Reusable pytest fixtures (auto-registered) | *(global, no import)* |
| `matchers/` | Custom assertion helpers | `tests._support.matchers` |

These complement (don't replace) `tests/factories/` — the canonical per-domain
factories still live there; `_support/factories/` re-exports the common ones and
adds those `tests/factories/` lacks (e.g. onboarding).

## Builders

```python
from tests._support.builders import AuthContextBuilder, SchoolApplicationBuilder

auth = AuthContextBuilder().as_superadmin().for_school(school.id).build()
app  = SchoolApplicationBuilder().micro_school().with_email("x@y.ma").as_model()
body = SchoolApplicationBuilder().formal_school().as_payload()   # HTTP payload
```

## Matchers

```python
from tests._support.matchers import (
    assert_uuid, assert_success_envelope, assert_list_envelope,
    assert_error_envelope, assert_activation_url,
)

data  = assert_success_envelope(resp.json())
token = assert_activation_url(result["activation_url"], token=result["activation_token"])
assert_error_envelope(resp.json(), code="ERR-APP-404")
```

## Factories

```python
from tests._support.factories import (
    UserFactory, SchoolFactory, MembershipFactory,
    SchoolApplicationFactory,           # new — onboarding
)

app = await SchoolApplicationFactory.create(session, applicant_email="x@y.ma")
```

## Fixtures (global)

Registered via `pytest_plugins = ("tests._support.fixtures.common",)` in the root
`tests/conftest.py`, so they are available everywhere:

| Fixture | Yields |
|---|---|
| `auth_builder` | a fresh `AuthContextBuilder` |
| `application_builder` | a fresh `SchoolApplicationBuilder` |
| `build_auth` | `build_auth(role="TCH", school_id=…) -> AuthContext` |

```python
def test_x(build_auth):
    auth = build_auth("ADM", school_id=some_uuid)
```

The helpers are themselves covered by `tests/unit/test_support_helpers.py`.
