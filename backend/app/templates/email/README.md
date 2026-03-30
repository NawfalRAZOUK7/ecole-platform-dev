# Email Templates

Jinja2 HTML templates for transactional emails. All templates extend `base.html` for consistent branding.

## Files

- **base.html** — Base layout with Ecole Platform header, footer, and responsive styling
- **welcome.html** — New user welcome email
- **otp.html** — One-time password for 2FA verification
- **grade_published.html** — Grade notification sent to parents/students
- **invoice_reminder.html** — Payment due reminder
- **notification_alert.html** — Single notification alert
- **notification_digest.html** — Bundled daily/weekly notification digest

## Localization

Templates support fr/ar/en via Jinja2 variables. RTL layout is applied automatically for Arabic.
