# templates/ — Jinja2 HTML Templates

Email and report templates using Jinja2 templating engine. Separated by use case (email, reports) with inheritance and reusable components.

## Directory Structure

```
templates/
├── email/           # Email message templates
│   ├── base.html              # Email layout wrapper
│   ├── welcome.html           # Welcome email (new user)
│   ├── otp.html               # OTP code delivery
│   ├── grade_published.html   # Grade notification
│   ├── invoice_reminder.html  # Payment reminder
│   ├── notification_alert.html # Real-time notification
│   └── notification_digest.html # Digest summary email
│
└── reports/         # PDF report templates
    ├── base.html              # Report layout wrapper
    ├── student_report_card.html      # Student transcript
    ├── class_summary.html            # Class statistics
    ├── attendance_report.html        # Attendance summary
    ├── school_analytics.html         # School-wide KPIs
    └── billing_statement.html        # Invoice statement
```

## Email Templates

### base.html — Email Wrapper

Base template for all emails with:
- Header (school logo, branding)
- Navigation/links
- Footer (contact info, unsubscribe)
- Responsive CSS
- Email client compatibility

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
        }
        .header {
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 20px;
        }
        .content {
            padding: 30px 0;
        }
        .footer {
            border-top: 1px solid #e0e0e0;
            padding-top: 20px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        {% block header %}
        <div class="header">
            <h1>École Platform</h1>
        </div>
        {% endblock %}

        <div class="content">
            {% block content %}
            {# Subtemplate content #}
            {% endblock %}
        </div>

        {% block footer %}
        <div class="footer">
            <p>&copy; 2024 École Platform. All rights reserved.</p>
            <p>
                <a href="{{ unsubscribe_url }}">Unsubscribe</a> |
                <a href="{{ contact_url }}">Contact Support</a>
            </p>
        </div>
        {% endblock %}
    </div>
</body>
</html>
```

### welcome.html — New User Welcome

Welcome email sent during registration:

```html
{% extends "email/base.html" %}

{% block content %}
<h2>Welcome to École Platform!</h2>

<p>Hi {{ first_name }},</p>

<p>Your account has been created successfully. You can now log in with your credentials:</p>

<ul>
    <li><strong>Email:</strong> {{ email }}</li>
    <li><strong>School:</strong> {{ school_name }}</li>
    <li><strong>Role:</strong> {{ role_display_name }}</li>
</ul>

<h3>Get Started</h3>

<ol>
    <li>Log in to <a href="{{ login_url }}">École Platform</a></li>
    <li>Complete your profile information</li>
    <li>Set up 2FA for security</li>
    <li>Configure notification preferences</li>
</ol>

{% if needs_email_verification %}
<p><strong>Verify your email:</strong> Click the button below to verify your email address.</p>
<p>
    <a href="{{ verification_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">
        Verify Email
    </a>
</p>
{% endif %}

<p>Questions? Check our <a href="{{ help_url }}">help center</a> or contact <a href="mailto:support@ecole.ma">support</a>.</p>
{% endblock %}
```

### otp.html — One-Time Password

OTP delivery for password reset or 2FA:

```html
{% extends "email/base.html" %}

{% block content %}
<h2>Your Verification Code</h2>

<p>Hi {{ first_name }},</p>

<p>You requested a password reset for your École Platform account. Use the code below:</p>

<div style="text-align: center; margin: 30px 0;">
    <div style="
        font-size: 32px;
        font-weight: bold;
        letter-spacing: 3px;
        font-family: 'Courier New', monospace;
        background: #f5f5f5;
        padding: 20px;
        border-radius: 5px;
    ">
        {{ otp_code }}
    </div>
</div>

<p><strong>This code expires in {{ expiry_minutes }} minutes.</strong></p>

<p>If you didn't request this code, ignore this email. Your account is safe.</p>

<p><strong>Security tip:</strong> Never share this code with anyone. Staff will never ask for it.</p>
{% endblock %}
```

### grade_published.html — Grade Notification

Notify students of published grades:

```html
{% extends "email/base.html" %}

{% block content %}
<h2>Your Grade Has Been Published</h2>

<p>Hi {{ student_name }},</p>

<p>Your teacher has published grades for <strong>{{ assignment_name }}</strong> in {{ course_name }}.</p>

<h3>Your Results</h3>

<table style="width: 100%; border-collapse: collapse;">
    <tr style="background: #f5f5f5; border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Score</td>
        <td style="padding: 10px; text-align: right;"><strong>{{ score }}/{{ max_score }}</strong></td>
    </tr>
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Percentage</td>
        <td style="padding: 10px; text-align: right;"><strong>{{ percentage }}%</strong></td>
    </tr>
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Grade</td>
        <td style="padding: 10px; text-align: right;"><strong>{{ grade_letter }}</strong></td>
    </tr>
</table>

{% if feedback %}
<h3>Teacher Feedback</h3>
<p style="background: #f9f9f9; padding: 15px; border-left: 4px solid #007bff;">
    {{ feedback }}
</p>
{% endif %}

<p>
    <a href="{{ view_grade_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">
        View Full Details
    </a>
</p>

<p>Questions? Ask your teacher or contact <a href="mailto:support@ecole.ma">support</a>.</p>
{% endblock %}
```

### invoice_reminder.html — Payment Reminder

Remind parents of unpaid invoices:

```html
{% extends "email/base.html" %}

{% block content %}
<h2>Payment Reminder</h2>

<p>Dear {{ parent_name }},</p>

<p>This is a friendly reminder that an invoice for {{ student_name }} is due for payment.</p>

<h3>Invoice Details</h3>

<table style="width: 100%; border-collapse: collapse;">
    <tr style="background: #f5f5f5; border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Invoice #</td>
        <td style="padding: 10px; text-align: right;">{{ invoice_number }}</td>
    </tr>
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Amount Due</td>
        <td style="padding: 10px; text-align: right;"><strong>{{ amount_mad }} MAD</strong></td>
    </tr>
    <tr style="border-bottom: 1px solid #ddd;">
        <td style="padding: 10px;">Due Date</td>
        <td style="padding: 10px; text-align: right;">{{ due_date }}</td>
    </tr>
</table>

{% if days_overdue > 0 %}
<p style="color: #d32f2f;">
    <strong>This invoice is {{ days_overdue }} days overdue.</strong>
</p>
{% endif %}

<h3>Pay Now</h3>

<p>
    <a href="{{ pay_url }}" style="background: #4caf50; color: white; padding: 12px 25px; text-decoration: none; font-size: 16px;">
        Pay Online Now
    </a>
</p>

<h3>Payment Methods</h3>

<ul>
    <li>Credit/Debit Card (online)</li>
    <li>Bank Transfer</li>
    <li>Cash at school office</li>
</ul>

<p>Questions about this invoice? <a href="{{ contact_url }}">Contact billing</a>.</p>
{% endblock %}
```

### notification_digest.html — Email Digest

Daily/weekly digest of notifications:

```html
{% extends "email/base.html" %}

{% block content %}
<h2>Your Daily Digest</h2>

<p>Hi {{ user_name }},</p>

<p>Here's a summary of updates from the past 24 hours:</p>

{% for notification in notifications %}
<div style="margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-left: 4px solid #2196f3;">
    <h4 style="margin-top: 0;">{{ notification.title }}</h4>
    <p>{{ notification.message }}</p>
    <a href="{{ notification.action_url }}">View Details</a>
</div>
{% endfor %}

<h3>Summary</h3>

<ul>
    <li>{{ grade_count }} grades published</li>
    <li>{{ assignment_count }} assignments due soon</li>
    <li>{{ message_count }} new messages</li>
    <li>{{ event_count }} upcoming events</li>
</ul>

<p>
    <a href="{{ dashboard_url }}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">
        View Dashboard
    </a>
</p>

<p>Manage <a href="{{ preferences_url }}">notification preferences</a> to customize this digest.</p>
{% endblock %}
```

## Report Templates

### base.html — Report Wrapper

Base template for PDF reports:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }
        h1 { color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 10px; }
        h2 { color: #2c5aa0; margin-top: 30px; }
        h3 { color: #4a7ba7; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f5f5f5;
            font-weight: bold;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        .footer {
            margin-top: 40px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ school_name }}</h1>
        <p>{{ report_title }}</p>
        <p>Generated on {{ report_date }}</p>
    </div>

    {% block content %}
    {# Report content #}
    {% endblock %}

    <div class="footer">
        <p>This report was generated on {{ report_date }} and is confidential.</p>
        <p>Page 1 of {{ total_pages }}</p>
    </div>
</body>
</html>
```

### student_report_card.html — Transcript

Student academic transcript:

```html
{% extends "templates/reports/base.html" %}

{% block content %}
<h2>Student Information</h2>

<table>
    <tr>
        <th>Name</th>
        <td>{{ student.first_name }} {{ student.last_name }}</td>
        <th>ID</th>
        <td>{{ student.id }}</td>
    </tr>
    <tr>
        <th>Class</th>
        <td>{{ class_name }}</td>
        <th>Academic Year</th>
        <td>{{ academic_year }}</td>
    </tr>
</table>

<h2>Grades</h2>

<table>
    <thead>
        <tr>
            <th>Course</th>
            <th>Teacher</th>
            <th>Score</th>
            <th>Percentage</th>
            <th>Grade</th>
            <th>Status</th>
        </tr>
    </thead>
    <tbody>
        {% for grade in grades %}
        <tr>
            <td>{{ grade.course_name }}</td>
            <td>{{ grade.teacher_name }}</td>
            <td>{{ grade.score }}/20</td>
            <td>{{ grade.percentage }}%</td>
            <td>{{ grade.letter }}</td>
            <td>{% if grade.is_passing %}✓ Pass{% else %}✗ Fail{% endif %}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<h3>Summary</h3>

<table>
    <tr>
        <th>GPA</th>
        <td>{{ gpa }}/20</td>
        <th>Overall Average</th>
        <td>{{ overall_average }}%</td>
    </tr>
    <tr>
        <th>Courses Passed</th>
        <td>{{ passed_count }}/{{ total_courses }}</td>
        <th>Status</th>
        <td>{{ overall_status }}</td>
    </tr>
</table>

<h2>Attendance</h2>

<table>
    <tr>
        <th>Total Days</th>
        <td>{{ total_days }}</td>
        <th>Days Present</th>
        <td>{{ days_present }}</td>
    </tr>
    <tr>
        <th>Absence Rate</th>
        <td>{{ absence_percentage }}%</td>
        <th>Status</th>
        <td>{% if attendance_okay %}Good{% else %}Poor{% endif %}</td>
    </tr>
</table>

<h2>Teacher Comments</h2>

<p>{{ teacher_comments }}</p>
{% endblock %}
```

### class_summary.html — Class Statistics

Class-level analytics report:

```html
{% extends "templates/reports/base.html" %}

{% block content %}
<h2>Class Overview</h2>

<table>
    <tr>
        <th>Class</th>
        <td>{{ class_name }}</td>
        <th>Teacher</th>
        <td>{{ teacher_name }}</td>
    </tr>
    <tr>
        <th>Total Students</th>
        <td>{{ total_students }}</td>
        <th>Academic Year</th>
        <td>{{ academic_year }}</td>
    </tr>
</table>

<h2>Grade Distribution</h2>

<table>
    <thead>
        <tr>
            <th>Grade Range</th>
            <th>Count</th>
            <th>Percentage</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>A (18-20)</td><td>{{ grade_a_count }}</td><td>{{ grade_a_pct }}%</td></tr>
        <tr><td>B (16-17.9)</td><td>{{ grade_b_count }}</td><td>{{ grade_b_pct }}%</td></tr>
        <tr><td>C (14-15.9)</td><td>{{ grade_c_count }}</td><td>{{ grade_c_pct }}%</td></tr>
        <tr><td>D (12-13.9)</td><td>{{ grade_d_count }}</td><td>{{ grade_d_pct }}%</td></tr>
        <tr><td>F (0-11.9)</td><td>{{ grade_f_count }}</td><td>{{ grade_f_pct }}%</td></tr>
    </tbody>
</table>

<h2>Performance Metrics</h2>

<table>
    <tr>
        <th>Class Average</th>
        <td>{{ class_average }}/20</td>
        <th>Pass Rate</th>
        <td>{{ pass_rate }}%</td>
    </tr>
    <tr>
        <th>Highest Score</th>
        <td>{{ highest_score }}/20</td>
        <th>Lowest Score</th>
        <td>{{ lowest_score }}/20</td>
    </tr>
</table>

<h2>Top Performers</h2>

<ol>
    {% for student in top_students %}
    <li>{{ student.name }}: {{ student.average }}/20</li>
    {% endfor %}
</ol>

<h2>Students Needing Support</h2>

<ol>
    {% for student in struggling_students %}
    <li>{{ student.name }}: {{ student.average }}/20</li>
    {% endfor %}
</ol>
{% endblock %}
```

## Usage in Services

Templates are rendered by the email service:

```python
# In email.py service
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("app/templates")
)

async def send_welcome_email(user: User):
    template = env.get_template("email/welcome.html")
    html = template.render(
        first_name=user.first_name,
        email=user.email,
        school_name=user.school.name,
        role_display_name=get_role_name(user),
        login_url="https://ecole.ma/login",
        verification_url=f"https://ecole.ma/verify/{user.verification_token}",
        help_url="https://help.ecole.ma",
        needs_email_verification=not user.is_verified
    )

    await send_email(
        to=user.email,
        subject="Welcome to École Platform",
        html=html
    )
```

PDF reports use WeasyPrint:

```python
# In reports.py service
from weasyprint import HTML

def generate_report_card_pdf(student_id: int) -> bytes:
    template = env.get_template("reports/student_report_card.html")
    html = template.render(
        student=student,
        class_name=class_name,
        academic_year=academic_year,
        grades=grades,
        gpa=gpa,
        teacher_comments=comments
    )

    pdf = HTML(string=html).write_pdf()
    return pdf
```

## Best Practices

1. **Inheritance** — Use base.html to avoid duplication
2. **Responsive** — Include viewport meta tag for email clients
3. **Fallback fonts** — Use web-safe fonts + fallbacks
4. **Accessibility** — Use semantic HTML, alt text for images
5. **Validation** — Always escape user input: `{{ content | escape }}`
6. **Testing** — Test in multiple email clients (Gmail, Outlook, etc.)
7. **Variables** — Document all required template variables
8. **Limits** — Keep email width 600px for compatibility

## Next Steps

- See `services/email.py` for email template rendering
- See `services/reports.py` for PDF report generation
- See Jinja2 docs: https://jinja.palletsprojects.com/
