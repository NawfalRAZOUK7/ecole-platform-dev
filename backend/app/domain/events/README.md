# Domain Events

Event classes for the event-driven architecture. Each event extends `BaseEvent` and is dispatched through the `EventDispatcher` service.

## Files

- **base.py** — `BaseEvent` abstract class with timestamp, actor, and payload
- **auth.py** — Authentication events (login, logout, password change, 2FA)
- **billing.py** — Billing events (invoice created, payment received, subscription changed)
- **calendar.py** — Calendar events (event created, RSVP updated)
- **documents.py** — Document events (uploaded, shared, deleted)
- **erp.py** — ERP events (timetable generated, resource allocated)
- **lms.py** — LMS events (grade published, assignment submitted, quiz completed)

## Usage

Events are created in service methods and dispatched via `EventDispatcher`. Subscribers (audit logger, notification hub, analytics) react asynchronously.
