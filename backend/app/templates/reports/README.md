# Report Templates

Jinja2 HTML templates rendered to PDF for printable school reports.

## Files

- **base.html** — Base report layout with school letterhead, page numbers, and print styling
- **student_report_card.html** — Individual student report card (grades, attendance, teacher comments)
- **class_summary.html** — Class-wide performance summary for teachers/directors
- **attendance_report.html** — Attendance statistics by class/student/period
- **school_analytics.html** — School-level KPI dashboard (enrollment, performance, billing)
- **billing_statement.html** — Invoice/payment statement for parents

## Generation

Reports are generated via the `ReportService` using WeasyPrint for HTML-to-PDF conversion. All monetary values use MAD, grades use the 0-20 scale.
