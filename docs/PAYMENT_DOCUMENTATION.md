# Payment Documentation — Invoice PDF, Receipts & Moroccan Compliance

> **Document Version**: 3.0
> **Last Updated**: 2026-05-05
> **Scope**: Invoice PDF generation, payment receipts, and Moroccan compliance requirements
> **Note**: This plan leverages existing ReportsService infrastructure to reduce coding effort

---

## Table of Contents

1. [Overview](#overview)
2. [Core Implementation Plan](#core-implementation-plan)
3. [Moroccan Compliance Enhancements](#moroccan-compliance-enhancements)
4. [Advanced Features](#advanced-features)
5. [Infrastructure Considerations](#infrastructure-considerations)
6. [Automation & Background Jobs](#automation--background-jobs)
7. [CI/CD Pipeline Changes](#cicd-pipeline-changes)
8. [Database Performance](#database-performance)
9. [Deployment Considerations](#deployment-considerations)
10. [Implementation Roadmap](#implementation-roadmap)
11. [Moroccan Market Requirements](#moroccan-market-requirements)
12. [Database Changes](#database-changes)
13. [API Changes](#api-changes)
14. [Frontend Changes](#frontend-changes)
15. [Testing](#testing)
16. [Rollback Procedure](#rollback-procedure)

---

## Overview

This document covers the complete payment documentation strategy for the École Platform, including:

- **Invoice PDF generation** - Professional invoices for parents and admins
- **Payment receipt PDFs** - Proof of payment documentation
- **Moroccan compliance** - TVA (tax) requirements, bilingual support
- **Advanced features** - Email attachments, archival, QR codes

### Core Features

- School branding (logo, name, contact details)
- Invoice details (number, date, due date, items, total)
- Banking/payment information (RIB, IBAN, BIC)
- Bilingual support (French/Arabic)
- TVA compliance (HT/TVA/TTC breakdown)
- Payment receipts with transaction details

---

## Core Implementation Plan

### Phase 1: Backend Foundation

**Note**: Leverage existing ReportsService infrastructure (`backend/app/services/reports.py`) which already includes:

- WeasyPrint integration for PDF generation
- Jinja2 template rendering with multi-language support (French/Arabic/English)
- RTL support for Arabic templates
- MinIO storage integration
- JWT-based download token security
- Report job system with caching

**Required changes**:

- Add banking details fields to School model
- Create database migration
- Add new report types to ReportType enum (INVOICE_PDF, PAYMENT_RECEIPT)
- Add invoice/receipt context builders to ReportsService
- Create HTML invoice template (French) extending existing base template
- Create HTML payment receipt template (French) extending existing base template

### Phase 2: API Integration

**Note**: Reuse existing ReportsService download infrastructure:

- Use existing `/reports/{job_id}/download` endpoint with JWT tokens
- Add invoice/receipt report type handling to ReportsService
- Leverage existing download token security
- Use existing MinIO storage and caching

**Required changes**:

- Add invoice PDF submission to ReportsService
- Add payment receipt submission to ReportsService
- Add context builders for invoice/receipt data

### Phase 3: Frontend Integration

- Add "Download PDF" button to web invoice detail page
- Add PDF download to mobile invoice screen
- Add "Download Receipt" button to payment screens
- Handle download errors

### Phase 4: Testing & QA

- Unit tests for PDF generation
- Integration tests for API endpoints
- Manual QA for web and mobile
- Performance testing for large invoice lists

---

## Moroccan Compliance Enhancements

### 1. TVA (Tax) Invoice Compliance

**Required Database Fields**:

```sql
-- Add to schools table
ALTER TABLE schools ADD COLUMN tva_number VARCHAR(50);
ALTER TABLE schools ADD COLUMN tax_id VARCHAR(50);
```

**InvoiceItem Model Enhancement**:

```python
class InvoiceItem(Base):
    # ... existing fields ...
    tva_rate: Mapped[float] = mapped_column(Float, default=0.0)  # 0%, 20%
    tva_amount: Mapped[float] = mapped_column(Float, default=0.0)
    amount_ht: Mapped[float] = mapped_column(Float)  # Hors Taxe
    amount_ttc: Mapped[float] = mapped_column(Float)  # Toutes Taxes Comprises
```

**Note**: TVA calculations should be applied during invoice generation in BillingService, not in PDF rendering.

**Invoice Template Enhancement**:

```html
<!-- TVA Breakdown Section -->
<table class="tva-table">
  <tr>
    <th>Description</th>
    <th>Montant HT</th>
    <th>TVA (%)</th>
    <th>Montant TVA</th>
    <th>Montant TTC</th>
  </tr>
  {% for item in invoice.items %}
  <tr>
    <td>{{ item.description }}</td>
    <td>{{ item.amount_ht }} {{ invoice.currency }}</td>
    <td>{{ item.tva_rate }}%</td>
    <td>{{ item.tva_amount }} {{ invoice.currency }}</td>
    <td>{{ item.amount_ttc }} {{ invoice.currency }}</td>
  </tr>
  {% endfor %}
</table>

<!-- TVA Footer -->
<div class="tva-footer">
  <p>TVA Number: {{ school.tva_number }}</p>
  <p>Identification Fiscale: {{ school.tax_id }}</p>
  <p>Facture établie conformément à la réglementation fiscale marocaine</p>
</div>
```

---

### 2. Multi-Language Invoice Templates

**Note**: ReportsService already has multi-language support with `lang` and `is_rtl` context variables. Leverage existing infrastructure.

**Template Structure** (extend existing ReportsService templates):

```
backend/app/templates/reports/
├── base.html  # Already exists with multi-language support
├── invoice_fr.html  # French invoice template (extends base.html)
├── invoice_ar.html  # Arabic invoice template (extends base.html)
├── payment_receipt_fr.html  # French receipt template (extends base.html)
└── payment_receipt_ar.html  # Arabic receipt template (extends base.html)
```

**Language Support**: Already implemented in ReportsService:

- `lang` parameter (fr, ar, en)
- `is_rtl` flag for Arabic templates
- Existing formatter functions: `fmt_date`, `fmt_datetime`, `fmt_number`

---

### 3. School Branding Customization

**Database Fields**:

```sql
-- Add to schools table
ALTER TABLE schools ADD COLUMN brand_color VARCHAR(7);  -- Hex color
ALTER TABLE schools ADD COLUMN footer_text TEXT;
ALTER TABLE schools ADD COLUMN stamp_image_url TEXT;
ALTER TABLE schools ADD COLUMN signature_image_url TEXT;
```

**Template Enhancement**:

```html
<style>
  :root {
      --brand-color: {{ school.brand_color or '#0066cc' }};
  }
  .header {
      background-color: var(--brand-color);
  }
</style>

<!-- School Stamp -->
{% if school.stamp_image_url %}
<img src="{{ school.stamp_image_url }}" class="stamp" alt="School Stamp" />
{% endif %}

<!-- Signature -->
{% if school.signature_image_url %}
<img
  src="{{ school.signature_image_url }}"
  class="signature"
  alt="Director Signature"
/>
{% endif %}
```

---

## Advanced Features

### 1. PDF Watermarking

**Template Enhancement**:

```python
{% if invoice.status == "pending" %}
<div class="watermark draft">BROUILLON</div>
{% elif invoice.status == "paid" %}
<div class="watermark paid">PAYÉ</div>
{% elif invoice.status == "cancelled" %}
<div class="watermark cancelled">ANNULÉ</div>
{% endif %}
```

**CSS**:

```css
.watermark {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  font-size: 120px;
  font-weight: bold;
  opacity: 0.1;
  pointer-events: none;
  z-index: 1000;
}

.watermark.draft {
  color: #666;
}
.watermark.paid {
  color: #00aa00;
}
.watermark.cancelled {
  color: #aa0000;
}
```

---

### 2. PDF Email Attachment

**Service Function**:

```python
# File: backend/app/services/invoice_pdf.py

async def email_invoice_pdf(
    invoice_id: str,
    recipient_email: str,
    language: str = "fr",
    db: AsyncSession = Depends(get_db),
):
    """Generate and email invoice PDF."""
    pdf_bytes = await generate_invoice_pdf(invoice_id, db, language)

    # Send email with PDF attachment
    await enqueue_email(
        to=recipient_email,
        template_name="invoice_with_pdf",
        language=language,
        pdf_attachment=pdf_bytes,
        pdf_filename=f"invoice_{invoice_id}.pdf",
        # ... other context
    )
```

**Email Template**:

```html
<!-- Subject: Votre facture N° {{ invoice_number }} -->

<p>Bonjour {{ parent_name }},</p>
<p>Veuillez trouver ci-joint votre facture N° {{ invoice_number }}.</p>
<p>Montant: {{ invoice.total_amount }} {{ invoice.currency }}</p>
<p>Date d'échéance: {{ invoice.due_date }}</p>
```

---

### 3. PDF Archival and Storage

**Note**: ReportsService already has MinIO storage integration, caching, and archival. No additional implementation needed.

**Existing Features**:

- Automatic MinIO storage via `storage.save()`
- Report caching with TTL (configurable)
- Automatic cleanup of expired reports
- File path tracking in ReportJob model

---

### 4. Bulk PDF Generation

**Note**: Bulk generation can be handled by submitting multiple report jobs via ReportsService. No separate batch implementation needed.

**Implementation**:

- Frontend submits multiple report generation requests
- Each PDF is generated independently with caching
- Frontend downloads each PDF via existing download endpoint

---

### 5. Payment Plan Installment Receipts

**Service Function**:

```python
async def generate_installment_receipt_pdf(
    installment_id: str,
    db: AsyncSession,
    language: str = "fr",
) -> bytes:
    """Generate receipt for a single installment payment."""
    installment = await get_installment_with_details(installment_id, db)

    # Render installment receipt template
    # Show: installment number, amount paid, remaining balance
    # Payment plan summary
    html = render_template("receipts/installment_receipt.html", installment=installment)

    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes
```

**Installment Receipt Content**:

- School header
- Payment plan reference
- Installment details (number, amount, due date, paid date)
- Payment method and transaction reference
- Summary: total plan amount, paid amount, remaining amount
- Next installment due date
- Payment schedule table

---

### 6. QR Code for Payment Verification

**Dependencies**:

```python
# Add to requirements.txt
qrcode>=7.4
```

**Service Function**:

```python
# File: backend/app/services/invoice_pdf.py

import qrcode

def generate_invoice_qr_code(invoice_id: str, base_url: str) -> bytes:
    """Generate QR code for invoice verification."""
    verification_url = f"{base_url}/invoices/{invoice_id}/verify"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for embedding in HTML
    from io import BytesIO
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
```

**Template Integration**:

```html
<div class="qr-code-section">
  <img src="data:image/png;base64,{{ qr_code_base64 }}" alt="Scan to verify" />
  <p>Scannez pour vérifier cette facture</p>
</div>
```

---

## Infrastructure Considerations

### MinIO Storage

**Note**: ReportsService already uses MinIO for PDF storage. No additional infrastructure setup needed.

**Existing Configuration**:

- Storage backend configured in `app/core/storage.py`
- PDFs stored in `reports/` subdirectory
- Automatic cleanup of expired reports via `cleanup_expired_reports()`

**Capacity Planning**:

- Estimate: 100 invoices/month × 50 KB = 5 MB/month per school
- For 100 schools: 500 MB/month
- With 7-year retention: ~42 GB total storage
- MinIO already configured for object storage - no changes needed

### Database Query Performance

**Note**: No new database queries added. PDF generation uses existing billing queries.

**Indexing**:

- Existing indexes on invoices table sufficient
- No new indexes required
- Invoice items already indexed by invoice_id

**Query Optimization**:

- Invoice fetch with items already optimized in BillingRepository
- No N+1 query issues expected
- Use existing `include_items=True` parameter

### Resource Requirements

**WeasyPrint Memory Usage**:

- Typical PDF generation: 50-100 MB RAM per generation
- Concurrent generations: limit to 2-3 concurrent jobs
- ARQ worker already configured - no changes needed

**Storage Bandwidth**:

- PDF upload: 50 KB per invoice
- Download: 50 KB per download
- Existing MinIO bandwidth sufficient

---

## Automation & Background Jobs

### ARQ Worker Integration

**Note**: ReportsService already uses ARQ worker for background PDF generation. No new worker setup needed.

**Existing Configuration**:

- ARQ worker already processes `generate_report_job` function
- Worker concurrency configured in `app/core/tasks.py`
- Automatic retry on failure already implemented

**No Changes Required**:

- ARQ worker already handles PDF generation jobs
- Existing error handling and retry logic sufficient
- Worker already deployed with backend

### Scheduled Jobs

**Existing Scheduled Jobs**:

- `cleanup_expired_reports()` - Already runs periodically
- No new scheduled jobs needed

**Optional Enhancement** (future):

- Scheduled PDF generation for all invoices at month-end
- Batch email of invoices to parents
- Not required for MVP

### Email Automation

**Note**: PDF email attachment uses existing email infrastructure.

**Existing Email Service**:

- `enqueue_email()` function already available
- Email templates in `app/templates/email/`
- SMTP configuration already in settings

**Implementation**:

- Add email trigger when invoice PDF is generated
- Use existing `invoice_with_pdf` template
- No new email infrastructure needed

---

## CI/CD Pipeline Changes

### GitHub Actions

**Note**: No CI/CD pipeline changes required for this feature.

**Existing CI Pipeline** (`.github/workflows/ci.yml`):

- Already tests billing service
- Already tests report generation
- No new test files needed - extend existing tests

**Existing Deployment Pipeline** (`.github/workflows/deploy-k8s.yml`):

- Already deploys backend with ARQ worker
- Already deploys MinIO
- No changes needed

**Testing in CI**:

- Add unit tests for invoice/receipt context builders
- Add integration tests for new report types
- Extend existing `test_billing_service.py` and `test_reports_service.py`

### Database Migration in CI

**Note**: Migration runs automatically in deployment pipeline.

**Existing Process**:

- Alembic migration runs on deployment
- No manual migration steps in CI
- Migration already part of Helm chart post-install hook

---

## Database Performance

### Migration Impact

**Migration File**: `g50_invoice_pdf_banking_details.py`

**Estimated Execution Time**:

- Adding 9 nullable columns to schools table: < 1 second
- Adding 4 columns to invoice_items table: < 1 second
- Total migration time: < 5 seconds for 100K records

**Zero Downtime**:

- All columns are nullable (no data required)
- No table locks during migration
- Can run during production hours

### Query Performance

**No New Queries**:

- Invoice PDF uses existing `get_invoice_by_id(include_items=True)`
- Payment receipt uses existing payment queries
- No performance degradation expected

**Existing Optimization**:

- Invoice items already use foreign key indexes
- School data already cached in ReportsService
- No N+1 queries in context builders

### Storage Growth

**Invoice PDF Storage**:

- 50 KB per PDF
- 100 invoices/month × 100 schools = 500 MB/month
- With 7-year retention: ~42 GB
- MinIO already configured for this scale

**Report Job Table Growth**:

- 1 row per PDF generation
- 100 generations/month × 100 schools = 10K rows/month
- With 1-year retention: 120K rows
- Existing cleanup job handles expired reports

---

## Deployment Considerations

### Deployment Strategy

**No Service Restart Required**:

- Database migration can run independently
- New code backward compatible
- Can deploy during business hours

**Rollback Plan**:

- Revert database migration if issues detected
- Remove new report types from enum
- Remove context builders
- Frontend handles missing endpoints gracefully

### Monitoring

**Existing Metrics**:

- Prometheus metrics already track report generation
- Existing `report_generation_duration_seconds` metric
- Existing `report_generation_success_total` metric

**New Metrics** (optional):

- Track invoice PDF generation count
- Track payment receipt generation count
- Not required for MVP

### Configuration

**Environment Variables**:

- No new environment variables required
- Uses existing `MINIO_*` variables
- Uses existing `JWT_SECRET_KEY` for download tokens

**Feature Flags**:

- Can use existing feature toggle system
- Enable/disable invoice PDF per school
- Not required for MVP

---

## Implementation Roadmap

### Phase 1: Core PDF Features (Week 1)

**Database Migration**:

**File**: `backend/alembic/versions/g50_invoice_pdf_banking_details.py`

```python
"""Add banking details to schools table for invoice PDF generation."""

revision = 'g50_invoice_pdf_banking_details'
down_revision = 'g49_program_management_and_history'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('schools', sa.Column('rib', sa.String(50), nullable=True))
    op.add_column('schools', sa.Column('iban', sa.String(34), nullable=True))
    op.add_column('schools', sa.Column('bic', sa.String(11), nullable=True))
    op.add_column('schools', sa.Column('bank_name', sa.String(255), nullable=True))
    op.add_column('schools', sa.Column('tva_number', sa.String(50), nullable=True))
    op.add_column('schools', sa.Column('tax_id', sa.String(50), nullable=True))
    op.add_column('schools', sa.Column('brand_color', sa.String(7), nullable=True))
    op.add_column('schools', sa.Column('footer_text', sa.TEXT, nullable=True))
    op.add_column('schools', sa.Column('stamp_image_url', sa.TEXT, nullable=True))
    op.add_column('schools', sa.Column('signature_image_url', sa.TEXT, nullable=True))

def downgrade():
    op.drop_column('schools', 'signature_image_url')
    op.drop_column('schools', 'stamp_image_url')
    op.drop_column('schools', 'footer_text')
    op.drop_column('schools', 'brand_color')
    op.drop_column('schools', 'tax_id')
    op.drop_column('schools', 'tva_number')
    op.drop_column('schools', 'bank_name')
    op.drop_column('schools', 'bic')
    op.drop_column('schools', 'iban')
    op.drop_column('schools', 'rib')
```

**Dependencies**:

**File**: `backend/requirements.txt`

WeasyPrint is already installed. Add:

```
qrcode>=7.4
```

**School Model Update**:

**File**: `backend/app/models/school.py`

```python
class School(TimestampMixin, SoftDeleteMixin, Base):
    # ... existing fields ...

    # Invoice PDF banking details
    rib: Mapped[str | None] = mapped_column(String(50), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    bic: Mapped[str | None] = mapped_column(String(11), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # TVA compliance
    tva_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Branding
    brand_color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    footer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    stamp_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**InvoiceItem Model Update**:

**File**: `backend/app/models/billing.py`

```python
class InvoiceItem(Base):
    # ... existing fields ...
    tva_rate: Mapped[float] = mapped_column(Float, default=0.0)
    tva_amount: Mapped[float] = mapped_column(Float, default=0.0)
    amount_ht: Mapped[float] = mapped_column(Float)
    amount_ttc: Mapped[float] = mapped_column(Float)
```

**ReportType Enum Extension**:

**File**: `backend/app/models/reporting.py`

```python
class ReportType(str, Enum):
    # ... existing report types ...
    INVOICE_PDF = "invoice_pdf"
    PAYMENT_RECEIPT = "payment_receipt"
```

**ReportsService Extension**:

**File**: `backend/app/services/reports.py`

```python
# Add to ReportsService class
async def _invoice_pdf_context(self, job: ReportJob) -> dict[str, Any]:
    """Build context for invoice PDF generation."""
    invoice_id = uuid.UUID(job.parameters["invoice_id"])
    # Fetch invoice with items, school, parent, student
    # Build context with all invoice data
    # Include sibling discount breakdown
    return context

async def _payment_receipt_context(self, job: ReportJob) -> dict[str, Any]:
    """Build context for payment receipt PDF generation."""
    payment_id = uuid.UUID(job.parameters["payment_id"])
    # Fetch payment attempt with invoice and school
    # Build context with payment details
    return context
```

**HTML Templates**:

**File**: `backend/app/templates/reports/invoice_fr.html`

```html
{% extends "reports/base.html" %} {% block content %}
<!-- School header -->
<!-- Invoice header -->
<!-- Parent information -->
<!-- Line items table with TVA breakdown -->
<!-- Sibling discount breakdown -->
<!-- Total amount (HT, TVA, TTC) -->
<!-- Banking details section -->
<!-- Payment instructions -->
<!-- TVA footer -->
<!-- Footer with school branding -->
{% endblock %}
```

**File**: `backend/app/templates/reports/invoice_ar.html`

Same structure, RTL layout, Arabic fonts.

**File**: `backend/app/templates/reports/payment_receipt_fr.html`

```html
{% extends "reports/base.html" %} {% block content %}
<!-- School header -->
<!-- Receipt header -->
<!-- Payment details -->
<!-- Invoice reference -->
<!-- Parent information -->
<!-- Banking/payment confirmation -->
<!-- Footer -->
{% endblock %}
```

---

### Phase 2: API Integration (Week 1)

**Invoice PDF Submission**:

**File**: `backend/app/api/v1/invoices.py`

```python
@router.post(
    "/{invoice_id}/pdf",
    summary="Generate invoice PDF",
    response_description="Report job for PDF generation",
)
async def generate_invoice_pdf(
    invoice_id: uuid.UUID,
    language: str = "fr",
    auth: AuthContext = Depends(requires_permission("PERM-BIL:invoice:read")),
    db: AsyncSession = Depends(get_db),
):
    """Submit invoice PDF generation job to ReportsService."""
    from app.services.reports import ReportsService
    from app.schemas.reports import ReportGenerateRequest

    reports = ReportsService(db)
    request = ReportGenerateRequest(
        type="invoice_pdf",
        locale=language,
        invoice_id=str(invoice_id),
    )

    job, cached = await reports.submit_report_job(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
        request=request,
    )
    return job
```

**Payment Receipt Submission**:

**File**: `backend/app/api/v1/payments.py`

```python
@router.post(
    "/{payment_id}/receipt",
    summary="Generate payment receipt PDF",
    response_description="Report job for PDF generation",
)
async def generate_payment_receipt(
    payment_id: uuid.UUID,
    language: str = "fr",
    auth: AuthContext = Depends(requires_permission("PERM-BIL:payment:read")),
    db: AsyncSession = Depends(get_db),
):
    """Submit payment receipt PDF generation job to ReportsService."""
    from app.services.reports import ReportsService
    from app.schemas.reports import ReportGenerateRequest

    reports = ReportsService(db)
    request = ReportGenerateRequest(
        type="payment_receipt",
        locale=language,
        payment_id=str(payment_id),
    )

    job, cached = await reports.submit_report_job(
        school_id=auth.school_id,
        requester_id=auth.user_id,
        requester_role=auth.role,
        request=request,
    )
    return job
```

---

### Phase 3: Multi-Language & Branding (Week 2)

- Create Arabic RTL template
- Add language selection logic
- Add school branding fields (already in migration)
- Implement color scheme customization
- Add stamp/signature upload support

---

### Phase 4: Email & Archival (Week 3)

- Add PDF email attachment support
- Implement MinIO archival
- Add PDF URL tracking in database
- Implement PDF regeneration logic
- Add watermarking support

---

### Phase 5: Advanced Features (Week 4)

- Add bulk PDF generation
- Implement QR code verification
- Add installment receipts
- Implement payment plan summary documents

---

## Moroccan Market Requirements

### Legal Requirements

- **TVA Number**: Required for all invoices (Numéro d'Identification Fiscale)
- **TVA Rate**: 20% for services (education may have exemptions)
- **Invoice Format**: Must include "Facture" header, TVA breakdown
- **Retention**: 7 years for financial records
- **Language**: French and Arabic required

### Cultural Considerations

- **RTL Layout**: Arabic templates must be right-to-left
- **Date Format**: Gregorian calendar, optionally Islamic calendar
- **Currency**: MAD (Moroccan Dirham) formatting
- **Payment Methods**: Cash, bank transfer, mobile money (Orange Money)

---

## Database Changes Summary

### Schools Table

| Column                | Type         | Nullable | Description                  |
| --------------------- | ------------ | -------- | ---------------------------- |
| `rib`                 | VARCHAR(50)  | YES      | Bank RIB number              |
| `iban`                | VARCHAR(34)  | YES      | IBAN (international)         |
| `bic`                 | VARCHAR(11)  | YES      | BIC/SWIFT code               |
| `bank_name`           | VARCHAR(255) | YES      | Bank name                    |
| `tva_number`          | VARCHAR(50)  | YES      | TVA number                   |
| `tax_id`              | VARCHAR(50)  | YES      | Tax identification number    |
| `brand_color`         | VARCHAR(7)   | YES      | Hex brand color              |
| `footer_text`         | TEXT         | YES      | Custom footer text           |
| `stamp_image_url`     | TEXT         | YES      | School stamp image URL       |
| `signature_image_url` | TEXT         | YES      | Director signature image URL |

### InvoiceItems Table

| Column       | Type  | Nullable | Description            |
| ------------ | ----- | -------- | ---------------------- |
| `tva_rate`   | FLOAT | NO       | TVA rate (0%, 20%)     |
| `tva_amount` | FLOAT | NO       | TVA amount             |
| `amount_ht`  | FLOAT | NO       | Hors Taxe amount       |
| `amount_ttc` | FLOAT | NO       | Toutes Taxes Comprises |

### Invoices Table (Archival)

| Column             | Type                     | Nullable | Description              |
| ------------------ | ------------------------ | -------- | ------------------------ |
| `pdf_url`          | TEXT                     | YES      | MinIO storage URL        |
| `pdf_generated_at` | TIMESTAMP WITH TIME ZONE | YES      | PDF generation timestamp |
| `pdf_version`      | INTEGER                  | NO       | PDF version number       |

---

## API Changes Summary

### New Endpoints

| Method | Path                             | Permission              | Description                       |
| ------ | -------------------------------- | ----------------------- | --------------------------------- |
| POST   | `/invoices/{invoice_id}/pdf`     | `PERM-BIL:invoice:read` | Submit invoice PDF generation job |
| POST   | `/payments/{payment_id}/receipt` | `PERM-BIL:payment:read` | Submit receipt PDF generation job |

### Existing Endpoints (Reused)

| Method | Path                         | Description                       |
| ------ | ---------------------------- | --------------------------------- |
| GET    | `/reports/{job_id}/download` | Download generated PDF (existing) |
| GET    | `/reports`                   | List report jobs (existing)       |

### Response

- **Content-Type**: `application/json` (job status)
- Download via existing `/reports/{job_id}/download` endpoint
- **Status Codes**:
  - `200` — Job submitted successfully
  - `403` — Permission denied
  - `404` — Invoice/payment not found
  - `500` — Job submission error

---

## Frontend Changes Summary

### Web (React)

**File**: `web/src/features/billing/InvoiceDetail.tsx`

Add download buttons:

```tsx
<Button onClick={handleDownloadPdf}>Download PDF</Button>
<Button onClick={handleDownloadReceipt}>Download Receipt</Button>
```

### Mobile (Flutter)

**File**: `mobile/lib/features/billing/invoice_detail_screen.dart`

Add download buttons and PDF save logic:

```dart
ElevatedButton.icon(
  icon: Icon(Icons.picture_as_pdf),
  label: Text('Télécharger PDF'),
  onPressed: _downloadPdf,
)
```

---

## Testing

### Unit Tests

**File**: `backend/tests/unit/services/test_invoice_pdf.py`

- Test PDF generation with valid invoice
- Test PDF generation with missing school data
- Test template rendering with bilingual content
- Test banking details inclusion
- Test TVA breakdown calculation
- Test QR code generation

### Integration Tests

**File**: `backend/tests/integration/api/test_invoice_pdf_api.py`

- Test `/invoices/{invoice_id}/pdf` endpoint
- Test `/payments/{payment_id}/receipt` endpoint
- Test PAR can download own invoice/receipt
- Test PAR cannot download other parent's documents
- Test ADM can download any document
- Test 404 for non-existent documents
- Test 403 for permission denied
- Test language parameter (fr/ar)

### Manual QA

**Web:**

1. Login as parent
2. Navigate to invoice list
3. Click on an invoice
4. Click "Download PDF"
5. Verify PDF downloads with correct data
6. Verify banking details are shown
7. Verify TVA breakdown is correct
8. Test Arabic language option

**Mobile (Android/iOS):**

1. Login as parent
2. Navigate to invoice screen
3. Click on an invoice
4. Tap "Download PDF"
5. Verify PDF saves to device
6. Open PDF and verify content
7. Test with large invoice (many items)
8. Test receipt download

---

## Rollback Procedure

If issues arise after deployment:

### Immediate Rollback (API Only)

1. Remove or comment out the PDF endpoints in `invoices.py` and `payments.py`
2. Redeploy backend
3. Frontend download buttons will show error (handle gracefully)

### Full Rollback

1. Revert database migration:
   ```bash
   alembic downgrade g50_invoice_pdf_banking_details
   ```
2. Remove qrcode from `requirements.txt`
3. Remove invoice/receipt context builders from ReportsService
4. Remove INVOICE_PDF and PAYMENT_RECEIPT from ReportType enum
5. Remove HTML templates
6. Remove job submission endpoints from invoices.py and payments.py
7. Redeploy backend
8. Remove frontend download buttons

---

## Reference — Dependencies

| Package      | Version  | Purpose                 | Status            |
| ------------ | -------- | ----------------------- | ----------------- |
| `weasyprint` | >=60.0   | HTML to PDF conversion  | Already installed |
| `qrcode`     | >=7.4    | QR code generation      | To be added       |
| `jinja2`     | existing | Template rendering      | Already installed |
| `reportlab`  | existing | Fallback PDF generation | Already installed |

---

## Sibling Discount Display

**Note**: Sibling discount is already implemented in BillingService (`backend/app/services/billing.py`). The invoice PDF templates must display the applied discount breakdown.

**Existing Implementation**:

- `SiblingDiscountPolicy` model with configurable percentages
- Logic in `generate_invoices_from_fee_structure()` that applies discounts
- Invoice item descriptions include discount breakdown (e.g., "Tuition (manual 10%, sibling 20%)")

**Template Enhancement**:

```html
<!-- Discount Breakdown Section -->
{% if invoice.has_discounts %}
<table class="discount-table">
  <tr>
    <th>Description</th>
    <th>Original Amount</th>
    <th>Discount Type</th>
    <th>Discount %</th>
    <th>Discount Amount</th>
    <th>Final Amount</th>
  </tr>
  {% for item in invoice.items %} {% if item.applied_discounts %}
  <tr>
    <td>{{ item.description }}</td>
    <td>{{ fmt_number(item.original_amount) }} {{ invoice.currency }}</td>
    <td>
      {% for discount in item.applied_discounts %} {{ discount.type }}{% if not
      loop.last %}, {% endif %} {% endfor %}
    </td>
    <td>{{ item.total_discount_percent }}%</td>
    <td>{{ fmt_number(item.discount_amount) }} {{ invoice.currency }}</td>
    <td>{{ fmt_number(item.amount) }} {{ invoice.currency }}</td>
  </tr>
  {% endif %} {% endfor %}
</table>
{% endif %}
```

**Context Builder Enhancement**:

```python
# In ReportsService._invoice_pdf_context()
context["has_discounts"] = any(
    item.applied_discounts for item in invoice.items
)
for item in invoice.items:
    # Parse discount from description (e.g., "Tuition (manual 10%, sibling 20%)")
    # Extract discount types and percentages
    # Calculate original amount, discount amount
```

## Reference — Permissions

| Permission              | Roles    | Description                               |
| ----------------------- | -------- | ----------------------------------------- |
| `PERM-BIL:invoice:read` | PAR, ADM | Read invoice details and generate PDF     |
| `PERM-BIL:payment:read` | PAR, ADM | Read payment details and generate receipt |
| `PERM-REP:download`     | All      | Download generated reports (existing)     |

---

## Reference — File Structure

```
backend/
├── alembic/versions/
│   └── g50_invoice_pdf_banking_details.py  # Migration
├── app/
│   ├── models/
│   │   ├── school.py                        # Add banking/branding fields
│   │   ├── billing.py                       # Add TVA fields to InvoiceItem
│   │   └── reporting.py                     # Add INVOICE_PDF, PAYMENT_RECEIPT to ReportType
│   ├── services/
│   │   └── reports.py                       # Add invoice/receipt context builders
│   ├── templates/
│   │   └── reports/
│   │       ├── base.html                    # Already exists
│   │       ├── invoice_fr.html             # French invoice template (new)
│   │       ├── invoice_ar.html             # Arabic invoice template (new)
│   │       ├── payment_receipt_fr.html     # French receipt template (new)
│   │       └── payment_receipt_ar.html     # Arabic receipt template (new)
│   └── api/v1/
│       ├── invoices.py                     # Add PDF job submission endpoint
│       └── payments.py                     # Add receipt job submission endpoint
└── requirements.txt                         # Add qrcode

web/
└── src/features/billing/
    └── InvoiceDetail.tsx                    # Add download buttons (submit job, poll status, download)

mobile/
└── lib/features/billing/
    └── invoice_detail_screen.dart           # Add download buttons (submit job, poll status, download)
```
