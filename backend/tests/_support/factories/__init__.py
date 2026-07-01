"""Single import surface for test factories.

Re-exports the most-used domain factories from ``tests/factories/`` and adds the
onboarding factories defined here, so a test can write::

    from tests._support.factories import (
        UserFactory, SchoolFactory, MembershipFactory, SchoolApplicationFactory,
    )

The per-domain factories still live in ``tests/factories/`` (their canonical
home); this package is a convenience aggregator plus the home for factories that
``tests/factories/`` does not yet provide (e.g. onboarding).
"""

from __future__ import annotations

# Onboarding factories (new — defined in this package)
from tests._support.factories.onboarding import (
    SchoolApplicationAttachmentFactory,
    SchoolApplicationFactory,
)

# Common existing factories (re-exported for a single import surface)
from tests.factories.erp import (
    AcademicYearFactory,
    ClassFactory,
    EnrollmentFactory,
)
from tests.factories.iam import (
    MembershipFactory,
    ParentChildLinkFactory,
    UserFactory,
)
from tests.factories.school import SchoolFactory

__all__ = [
    # onboarding
    "SchoolApplicationFactory",
    "SchoolApplicationAttachmentFactory",
    # iam
    "UserFactory",
    "MembershipFactory",
    "ParentChildLinkFactory",
    # school / erp
    "SchoolFactory",
    "AcademicYearFactory",
    "ClassFactory",
    "EnrollmentFactory",
]
