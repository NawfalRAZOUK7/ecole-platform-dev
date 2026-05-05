# Payment Documentation Implementation Guide

> **Document Version**: 1.0
> **Last Updated**: 2026-05-05
> **Purpose**: Step-by-step implementation prompts for invoice PDF, payment receipts, and Moroccan compliance features

---

## Table of Contents

1. [Phase 1: Database & Model Changes](#phase-1-database--model-changes)
2. [Phase 2: ReportsService Extensions](#phase-2-reportsservice-extensions)
3. [Phase 3: HTML Templates](#phase-3-html-templates)
4. [Phase 4: API Endpoints](#phase-4-api-endpoints)
5. [Phase 5: Frontend Integration](#phase-5-frontend-integration)
6. [Phase 6: Testing](#phase-6-testing)
7. [Phase 7: Deployment](#phase-7-deployment)

---

## Phase 1: Database & Model Changes

### Prompt 1.1: Create Database Migration for Banking Details

**Objective**: Add banking, TVA, and branding fields to schools table; add TVA fields to invoice_items table.

**Steps**:

1. **Create migration file**
   - Generate new Alembic migration: `g50e_invoice_pdf_banking_details.py`
   - Set down_revision to latest migration
   - Add upgrade() and downgrade() functions

2. **Add schools table columns**
   - `rib` VARCHAR(50) - Bank RIB number
   - `iban` VARCHAR(34) - IBAN (international)
   - `bic` VARCHAR(11) - BIC/SWIFT code
   - `bank_name` VARCHAR(255) - Bank name
   - `tva_number` VARCHAR(50) - TVA number
   - `tax_id` VARCHAR(50) - Tax identification number
   - `brand_color` VARCHAR(7) - Hex brand color
   - `footer_text` TEXT - Custom footer text
   - `stamp_image_url` TEXT - School stamp image URL
   - `signature_image_url` TEXT - Director signature image URL

3. **Add invoice_items table columns**
   - `tva_rate` NUMERIC(5,2) DEFAULT 0.0 - TVA rate (0%, 20%)
   - `tva_amount` NUMERIC(12,2) DEFAULT 0.0 - TVA amount
   - `amount_ht` NUMERIC(12,2) - Hors Taxe amount
   - `amount_ttc` NUMERIC(12,2) - Toutes Taxes Comprises

4. **Make all columns nullable**
   - Ensures zero-downtime migration
   - Allows existing schools without banking details

**Checklist**:

- [x] Migration file created with correct revision number (`a1b2c3d4e5f7`)
- [x] All 10 schools table columns added in upgrade()
- [x] All 4 invoice_items table columns added in upgrade()
- [x] downgrade() function removes all added columns
- [x] All columns are nullable
- [x] Migration structure validated
- [x] Syntax validated with Python AST

---

### Prompt 1.2: Update School Model

**Objective**: Add banking, TVA, and branding fields to School model.

**Steps**:

1. **Open School model file**
   - File: `backend/app/models/school.py`

2. **Add banking details fields**
   - `rib: Mapped[str | None] = mapped_column(String(50), nullable=True)`
   - `iban: Mapped[str | None] = mapped_column(String(34), nullable=True)`
   - `bic: Mapped[str | None] = mapped_column(String(11), nullable=True)`
   - `bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)`

3. **Add TVA compliance fields**
   - `tva_number: Mapped[str | None] = mapped_column(String(50), nullable=True)`
   - `tax_id: Mapped[str | None] = mapped_column(String(50), nullable=True)`

4. **Add branding fields**
   - `brand_color: Mapped[str | None] = mapped_column(String(7), nullable=True)`
   - `footer_text: Mapped[str | None] = mapped_column(Text, nullable=True)`
   - `stamp_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)`
   - `signature_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)`

**Checklist**:

- [x] All 10 fields added to School model
- [x] All fields use `Mapped[str | None]` for nullable strings
- [x] Correct String lengths specified
- [x] Text type used for long text fields
- [x] Model passes type checking
- [x] No syntax errors

---

### Prompt 1.3: Update InvoiceItem Model

**Objective**: Add TVA fields to InvoiceItem model.

**Steps**:

1. **Open InvoiceItem model file**
   - File: `backend/app/models/billing.py`

2. **Add TVA fields**
   - `tva_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0.0)`
   - `tva_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0.0)`
   - `amount_ht: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)`
   - `amount_ttc: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)`

3. **Note**: These fields will be populated during invoice generation in BillingService

**Checklist**:

- [x] All 4 TVA fields added to InvoiceItem model
- [x] tva_rate and tva_amount have default=0.0
- [x] amount_ht and amount_ttc are required (nullable=False)
- [x] Numeric type used (consistent with codebase)
- [x] Model passes type checking
- [x] No syntax errors

---

### Prompt 1.4: Update ReportType Enum

**Objective**: Add INVOICE_PDF and PAYMENT_RECEIPT to ReportType enum.

**Steps**:

1. **Open ReportType enum file**
   - File: `backend/app/models/reporting.py`

2. **Add new report types**
   - `INVOICE_PDF = "invoice_pdf"`
   - `PAYMENT_RECEIPT = "payment_receipt"`

3. **Add to \_build_context() method**
   - Add case for INVOICE_PDF → `_invoice_pdf_context()`
   - Add case for PAYMENT_RECEIPT → `_payment_receipt_context()`

**Checklist**:

- [x] INVOICE_PDF added to enum
- [x] PAYMENT_RECEIPT added to enum
- [x] \_build_context() handles INVOICE_PDF case
- [x] \_build_context() handles PAYMENT_RECEIPT case
- [x] No duplicate enum values
- [x] Code compiles without errors

---

### Prompt 1.5: Add QRCode Dependency

**Objective**: Add qrcode package to requirements.txt.

**Steps**:

1. **Open requirements.txt**
   - File: `backend/requirements.txt`

2. **Add qrcode package**
   - `qrcode[pil]==8.0.*` (already present)

3. **Note**: WeasyPrint already installed, no need to add

**Checklist**:

- [x] qrcode>=7.4 present in requirements.txt (installed: 8.0.\*)
- [x] Version constraint specified (==8.0.\*)
- [x] No duplicate entries
- [x] PIL extra included for image support

---

## Phase 2: ReportsService Extensions

### Prompt 2.1: Add Invoice PDF Context Builder

**Objective**: Implement `_invoice_pdf_context()` method in ReportsService.

**Steps**:

1. **Open ReportsService file**
   - File: `backend/app/services/reports.py`

2. **Add \_invoice_pdf_context() method**
   - Accept job: ReportJob parameter
   - Extract invoice_id from job.parameters
   - Fetch invoice with items using BillingRepository
   - Fetch school data
   - Fetch parent data
   - Fetch student data
   - Build context dictionary with:
     - invoice details (number, date, due date, status)
     - invoice items with TVA breakdown
     - school details (name, address, contact, banking, TVA, branding)
     - parent information
     - student information
     - sibling discount breakdown
     - totals (HT, TVA, TTC)
     - language (from job.parameters["locale"])
     - is_rtl flag

3. **Parse sibling discounts from item descriptions**
   - Extract discount types and percentages
   - Calculate original amount, discount amount, final amount
   - Build applied_discounts array for each item

**Checklist**:

- [x] Method signature correct
- [x] Invoice fetched with items
- [x] School data fetched
- [x] Parent data fetched
- [x] Student data fetched (placeholder for children)
- [x] Context includes all invoice details
- [x] Context includes all school details
- [x] TVA breakdown calculated
- [x] Sibling discounts placeholder included
- [x] Language and RTL flags set
- [x] No N+1 queries (eager loading)
- [x] Error handling for missing data

---

### Prompt 2.2: Add Payment Receipt Context Builder

**Objective**: Implement `_payment_receipt_context()` method in ReportsService.

**Steps**:

1. **Open ReportsService file**
   - File: `backend/app/services/reports.py`

2. **Add \_payment_receipt_context() method**
   - Accept job: ReportJob parameter
   - Extract payment_id from job.parameters
   - Fetch payment attempt with invoice using BillingRepository
   - Fetch school data
   - Fetch parent data
   - Build context dictionary with:
     - payment details (amount, method, transaction reference, date)
     - invoice reference (number, date)
     - school details (name, address, contact, banking)
     - parent information
     - payment status
     - language (from job.parameters["locale"])
     - is_rtl flag

**Checklist**:

- [x] Method signature correct
- [x] Payment attempt fetched with invoice
- [x] School data fetched
- [x] Parent data fetched
- [x] Context includes all payment details
- [x] Context includes school details
- [x] Context includes invoice reference
- [x] Language and RTL flags set
- [x] No N+1 queries
- [x] Error handling for missing data

---

### Prompt 2.3: Add QR Code Generation Helper

**Objective**: Implement QR code generation for invoice verification.

**Steps**:

1. **Open ReportsService file**
   - File: `backend/app/services/reports.py`

2. **Add import**
   - `import qrcode`
   - `from io import BytesIO`
   - `import base64`

3. **Add helper method**
   - `_generate_qr_code(invoice_id: str, base_url: str) -> str`
   - Create verification URL: `{base_url}/invoices/{invoice_id}/verify`
   - Generate QR code with qrcode library
   - Convert to base64 string
   - Return base64 string for HTML embedding

4. **Call in \_invoice_pdf_context()**
   - Generate QR code for invoice
   - Add qr_code_base64 to context

**Checklist**:

- [x] qrcode imported
- [x] Helper method implemented
- [x] Verification URL constructed correctly
- [x] QR code generated successfully
- [x] Converted to base64
- [x] Called in invoice context builder
- [x] Added to context
- [x] Error handling for QR generation failure

---

### Prompt 2.4: Add Invoice PDF to Parameter Resolution

**Objective**: Add invoice PDF parameter resolution to `_resolve_parameters()`.

**Steps**:

1. **Open ReportsService file**
   - File: `backend/app/services/reports.py`

2. **Add case for INVOICE_PDF**
   - Check report_type == INVOICE_PDF
   - Validate invoice_id parameter
   - Fetch invoice to verify existence
   - Check permission: requester must be invoice owner or admin
   - Add invoice_id to parameters

**Checklist**:

- [x] INVOICE_PDF case added
- [x] invoice_id parameter validated
- [x] Invoice existence verified
- [x] Permission check implemented
- [x] invoice_id added to parameters
- [x] Error handling for invalid invoice_id
- [x] Error handling for permission denied

---

### Prompt 2.5: Add Payment Receipt to Parameter Resolution

**Objective**: Add payment receipt parameter resolution to `_resolve_parameters()`.

**Steps**:

1. **Open ReportsService file**
   - File: `backend/app/services/reports.py`

2. **Add case for PAYMENT_RECEIPT**
   - Check report_type == PAYMENT_RECEIPT
   - Validate payment_id parameter
   - Fetch payment attempt to verify existence
   - Check permission: requester must be payment owner or admin
   - Add payment_id to parameters

**Checklist**:

- [x] PAYMENT_RECEIPT case added
- [x] payment_id parameter validated
- [x] Payment attempt existence verified
- [x] Permission check implemented
- [x] payment_id added to parameters
- [x] Error handling for invalid payment_id
- [x] Error handling for permission denied

---

## Phase 3: HTML Templates

### Prompt 3.1: Create French Invoice Template

**Objective**: Create invoice_fr.html template extending base.html.

**Steps**:

1. **Create template file**
   - File: `backend/app/templates/reports/invoice_fr.html`
   - Extend: `{% extends "reports/base.html" %}`

2. **Add content block**
   - School header (logo, name, address, contact)
   - Invoice header (number, date, due date, status watermark)
   - Parent information section
   - Student information section
   - Invoice items table with columns:
     - Description
     - Montant HT
     - TVA (%)
     - Montant TVA
     - Montant TTC
   - Sibling discount breakdown table
   - Totals section (HT, TVA, TTC)
   - Banking details section (RIB, IBAN, BIC, bank_name)
   - Payment instructions
   - TVA footer (TVA number, tax ID, legal text)
   - Footer with school branding (color, stamp, signature)
   - QR code section

3. **Use existing formatters**
   - `{{ fmt_date(date) }}`
   - `{{ fmt_number(amount) }}`
   - `{{ fmt_datetime(datetime) }}`

**Checklist**:

- [x] Template extends base.html
- [x] School header section complete
- [x] Invoice header section complete
- [x] Parent information section complete
- [x] Student information section complete
- [x] Items table with TVA breakdown
- [x] Sibling discount table
- [x] Totals section (HT, TVA, TTC)
- [x] Banking details section
- [x] Payment instructions
- [x] TVA footer
- [x] School branding footer
- [x] QR code section
- [x] Formatters used correctly
- [x] French labels used
- [x] LTR layout

---

### Prompt 3.2: Create Arabic Invoice Template

**Objective**: Create invoice_ar.html template extending base.html with RTL layout.

**Steps**:

1. **Create template file**
   - File: `backend/app/templates/reports/invoice_ar.html`
   - Extend: `{% extends "reports/base.html" %}`
   - Add: `<html dir="rtl" lang="ar">`

2. **Add content block**
   - Same structure as French template
   - Arabic labels for all text
   - RTL layout for tables and sections
   - Arabic fonts (Noto Sans Arabic, Amiri)

3. **Use existing formatters**
   - `{{ fmt_date(date) }}`
   - `{{ fmt_number(amount) }}`
   - `{{ fmt_datetime(datetime) }}`

**Checklist**:

- [x] Template extends base.html
- [x] RTL direction set
- [x] Arabic language set
- [x] School header section complete (Arabic)
- [x] Invoice header section complete (Arabic)
- [x] Parent information section complete (Arabic)
- [x] Student information section complete (Arabic)
- [x] Items table with TVA breakdown (Arabic)
- [x] Sibling discount table (Arabic)
- [x] Totals section (Arabic)
- [x] Banking details section (Arabic)
- [x] Payment instructions (Arabic)
- [x] TVA footer (Arabic)
- [x] School branding footer
- [x] QR code section
- [x] Formatters used correctly
- [x] Arabic labels used
- [x] RTL layout applied

---

### Prompt 3.3: Create French Payment Receipt Template

**Objective**: Create payment_receipt_fr.html template extending base.html.

**Steps**:

1. **Create template file**
   - File: `backend/app/templates/reports/payment_receipt_fr.html`
   - Extend: `{% extends "reports/base.html" %}`

2. **Add content block**
   - School header (logo, name, address, contact)
   - Receipt header (receipt number, payment date)
   - Payment details (amount, method, transaction reference)
   - Invoice reference (invoice number, invoice date)
   - Parent information
   - Banking/payment confirmation
   - Footer with "Thank you for your payment"
   - School stamp/signature placeholder

3. **Use existing formatters**
   - `{{ fmt_date(date) }}`
   - `{{ fmt_number(amount) }}`
   - `{{ fmt_datetime(datetime) }}`

**Checklist**:

- [x] Template extends base.html
- [x] School header section complete
- [x] Receipt header section complete
- [x] Payment details section complete
- [x] Invoice reference section complete
- [x] Parent information section complete
- [x] Banking confirmation
- [x] Thank you footer
- [x] Stamp/signature placeholder
- [x] Formatters used correctly
- [x] French labels used
- [x] LTR layout

---

### Prompt 3.4: Create Arabic Payment Receipt Template

**Objective**: Create payment_receipt_ar.html template extending base.html with RTL layout.

**Steps**:

1. **Create template file**
   - File: `backend/app/templates/reports/payment_receipt_ar.html`
   - Extend: `{% extends "reports/base.html" %}`
   - Add: `<html dir="rtl" lang="ar">`

2. **Add content block**
   - Same structure as French template
   - Arabic labels for all text
   - RTL layout for tables and sections
   - Arabic fonts

3. **Use existing formatters**
   - `{{ fmt_date(date) }}`
   - `{{ fmt_number(amount) }}`
   - `{{ fmt_datetime(datetime) }}`

**Checklist**:

- [x] Template extends base.html
- [x] RTL direction set
- [x] Arabic language set
- [x] School header section complete (Arabic)
- [x] Receipt header section complete (Arabic)
- [x] Payment details section complete (Arabic)
- [x] Invoice reference section complete (Arabic)
- [x] Parent information section complete (Arabic)
- [x] Banking confirmation (Arabic)
- [x] Thank you footer (Arabic)
- [x] Stamp/signature placeholder
- [x] Formatters used correctly
- [x] Arabic labels used
- [x] RTL layout applied

---

## Phase 4: API Endpoints

### Prompt 4.1: Add Invoice PDF Submission Endpoint

**Objective**: Add POST endpoint to submit invoice PDF generation job.

**Steps**:

1. **Open invoices API file**
   - File: `backend/app/api/v1/invoices.py`

2. **Add endpoint**
   - Path: `/{invoice_id}/pdf`
   - Method: POST
   - Summary: "Generate invoice PDF"
   - Permission: `PERM-BIL:invoice:read`

3. **Implement endpoint logic**
   - Import ReportsService and ReportGenerateRequest
   - Create ReportsService instance
   - Build ReportGenerateRequest with:
     - type="invoice_pdf"
     - locale=language (from query param)
     - invoice_id=str(invoice_id)
   - Call reports.submit_report_job()
   - Return job response

4. **Add query parameter**
   - language: str = "fr" (default French)
   - Validate language is "fr" or "ar"

**Checklist**:

- [x] Endpoint path correct
- [x] POST method used
- [x] Permission check added
- [x] ReportsService imported
- [x] ReportGenerateRequest imported
- [x] Request built correctly
- [x] submit_report_job() called
- [x] Job response returned
- [x] Language query parameter added
- [x] Language validation added
- [x] Error handling for invalid invoice_id
- [x] Error handling for permission denied

---

### Prompt 4.2: Add Payment Receipt Submission Endpoint

**Objective**: Add POST endpoint to submit payment receipt PDF generation job.

**Steps**:

1. **Open payments API file**
   - File: `backend/app/api/v1/payments.py`

2. **Add endpoint**
   - Path: `/{payment_id}/receipt`
   - Method: POST
   - Summary: "Generate payment receipt PDF"
   - Permission: `PERM-BIL:payment:read`

3. **Implement endpoint logic**
   - Import ReportsService and ReportGenerateRequest
   - Create ReportsService instance
   - Build ReportGenerateRequest with:
     - type="payment_receipt"
     - locale=language (from query param)
     - payment_id=str(payment_id)
   - Call reports.submit_report_job()
   - Return job response

4. **Add query parameter**
   - language: str = "fr" (default French)
   - Validate language is "fr" or "ar"

**Checklist**:

- [x] Endpoint path correct
- [x] POST method used
- [x] Permission check added
- [x] ReportsService imported
- [x] ReportGenerateRequest imported
- [x] Request built correctly
- [x] submit_report_job() called
- [x] Job response returned
- [x] Language query parameter added
- [x] Language validation added
- [x] Error handling for invalid payment_id
- [x] Error handling for permission denied

---

## Phase 5: Frontend Integration

### Prompt 5.1: Add Web Invoice PDF Download Button

**Objective**: Add "Download PDF" button to web invoice detail page.

**Steps**:

1. **Open invoice detail component**
   - File: `web/src/features/billing/InvoiceDetail.tsx`

2. **Add download function**
   - `handleDownloadPdf(language: string)`
   - Call POST `/invoices/{invoice_id}/pdf` with language
   - Get job_id from response
   - Poll job status until READY
   - Download PDF from `/reports/{job_id}/download`

3. **Add UI button**
   - Button component with "Download PDF" label
   - Language selector (French/Arabic)
   - Loading state during generation
   - Error handling

**Checklist**:

- [x] Download function implemented
- [x] POST endpoint called correctly
- [x] Job polling implemented
- [x] Download from existing endpoint
- [x] Button added to UI
- [x] Language selector added
- [x] Loading state shown
- [x] Error handling added
- [x] Success feedback shown

---

### Prompt 5.2: Add Web Payment Receipt Download Button

**Objective**: Add "Download Receipt" button to web payment screens.

**Steps**:

1. **Open payment detail component**
   - File: `web/src/features/billing/PaymentDetail.tsx`

2. **Add download function**
   - `handleDownloadReceipt(language: string)`
   - Call POST `/payments/{payment_id}/receipt` with language
   - Get job_id from response
   - Poll job status until READY
   - Download PDF from `/reports/{job_id}/download`

3. **Add UI button**
   - Button component with "Download Receipt" label
   - Language selector (French/Arabic)
   - Loading state during generation
   - Error handling

**Checklist**:

- [x] Download function implemented
- [x] POST endpoint called correctly
- [x] Job polling implemented
- [x] Download from existing endpoint
- [x] Button added to UI
- [x] Language selector added
- [x] Loading state shown
- [x] Error handling added
- [x] Success feedback shown

---

### Prompt 5.3: Add Mobile Invoice PDF Download Button

**Objective**: Add "Download PDF" button to mobile invoice detail screen.

**Steps\*\***

1. **Open invoice detail screen**
   - File: `mobile/lib/features/billing/invoice_detail_screen.dart`

2. **Add download function**
   - `_downloadPdf(String language)`
   - Call POST `/invoices/{invoice_id}/pdf` with language
   - Get job_id from response
   - Poll job status until READY
   - Download PDF from `/reports/{job_id}/download`
   - Save PDF to device

3. **Add UI button**
   - ElevatedButton with PDF icon
   - Label: "Télécharger PDF"
   - Language selector (French/Arabic)
   - Loading indicator
   - Error handling

**Checklist**:

- [x] Download function implemented
- [x] POST endpoint called correctly
- [x] Job polling implemented
- [x] Download from existing endpoint
- [x] PDF saved to device
- [x] Button added to UI
- [x] Language selector added
- [x] Loading indicator shown
- [x] Error handling added
- [x] Success feedback shown

---

### Prompt 5.4: Add Mobile Payment Receipt Download Button

**Objective**: Add "Download Receipt" button to mobile payment screens.

**Steps**:

1. **Open payment detail screen**
   - File: `mobile/lib/features/billing/payment_detail_screen.dart`

2. **Add download function**
   - `_downloadReceipt(String language)`
   - Call POST `/payments/{payment_id}/receipt` with language
   - Get job_id from response
   - Poll job status until READY
   - Download PDF from `/reports/{job_id}/download`
   - Save PDF to device

3. **Add UI button**
   - ElevatedButton with PDF icon
   - Label: "Télécharger Reçu"
   - Language selector (French/Arabic)
   - Loading indicator
   - Error handling

**Checklist**:

- [x] Download function implemented
- [x] POST endpoint called correctly
- [x] Job polling implemented
- [x] Download from existing endpoint
- [x] PDF saved to device
- [x] Button added to UI
- [x] Language selector added
- [x] Loading indicator shown
- [x] Error handling added
- [x] Success feedback shown

---

## Phase 6: Testing

### Prompt 6.1: Add Unit Tests for Invoice Context Builder

**Objective**: Write unit tests for \_invoice_pdf_context() method.

**Steps**:

1. **Create test file**
   - File: `backend/tests/unit/services/test_invoice_pdf_context.py`

2. **Add test cases**
   - Test with valid invoice and school
   - Test with missing school data
   - Test with missing parent data
   - Test TVA breakdown calculation
   - Test sibling discount parsing
   - Test language parameter (fr, ar)
   - Test RTL flag for Arabic

3. **Mock dependencies**
   - Mock BillingRepository
   - Mock storage
   - Mock database session

**Checklist**:

- [ ] Test file created
- [ ] Valid invoice test passes
- [ ] Missing school data test passes
- [ ] Missing parent data test passes
- [ ] TVA breakdown test passes
- [ ] Sibling discount test passes
- [ ] Language test passes
- [ ] RTL flag test passes
- [ ] All mocks configured
- [ ] Tests run successfully

---

### Prompt 6.2: Add Unit Tests for Receipt Context Builder

**Objective**: Write unit tests for \_payment_receipt_context() method.

**Steps**:

1. **Create test file**
   - File: `backend/tests/unit/services/test_payment_receipt_context.py`

2. **Add test cases**
   - Test with valid payment and invoice
   - Test with missing school data
   - Test with missing invoice data
   - Test language parameter (fr, ar)
   - Test RTL flag for Arabic

3. **Mock dependencies**
   - Mock BillingRepository
   - Mock database session

**Checklist**:

- [ ] Test file created
- [ ] Valid payment test passes
- [ ] Missing school data test passes
- [ ] Missing invoice data test passes
- [ ] Language test passes
- [ ] RTL flag test passes
- [ ] All mocks configured
- [ ] Tests run successfully

---

### Prompt 6.3: Add Integration Tests for Invoice PDF API

**Objective**: Write integration tests for invoice PDF submission endpoint.

**Steps**:

1. **Create test file**
   - File: `backend/tests/integration/api/test_invoice_pdf_api.py`

2. **Add test cases**
   - Test POST /invoices/{id}/pdf with valid invoice
   - Test with language=fr
   - Test with language=ar
   - Test PAR can download own invoice
   - Test PAR cannot download other parent's invoice
   - Test ADM can download any invoice
   - Test 404 for non-existent invoice
   - Test 403 for permission denied
   - Test invalid language parameter

3. **Setup test data**
   - Create test school
   - Create test invoice
   - Create test parent user

**Checklist**:

- [ ] Test file created
- [ ] Valid invoice test passes
- [ ] French language test passes
- [ ] Arabic language test passes
- [ ] Parent permission test passes
- [ ] Parent denied test passes
- [ ] Admin permission test passes
- [ ] 404 test passes
- [ ] 403 test passes
- [ ] Invalid language test passes
- [ ] Test data created
- [ ] Tests run successfully

---

### Prompt 6.4: Add Integration Tests for Receipt API

**Objective**: Write integration tests for payment receipt submission endpoint.

**Steps**:

1. **Create test file**
   - File: `backend/tests/integration/api/test_payment_receipt_api.py`

2. **Add test cases**
   - Test POST /payments/{id}/receipt with valid payment
   - Test with language=fr
   - Test with language=ar
   - Test PAR can download own receipt
   - Test PAR cannot download other parent's receipt
   - Test ADM can download any receipt
   - Test 404 for non-existent payment
   - Test 403 for permission denied
   - Test invalid language parameter

3. **Setup test data**
   - Create test school
   - Create test payment
   - Create test parent user

**Checklist**:

- [ ] Test file created
- [ ] Valid payment test passes
- [ ] French language test passes
- [ ] Arabic language test passes
- [ ] Parent permission test passes
- [ ] Parent denied test passes
- [ ] Admin permission test passes
- [ ] 404 test passes
- [ ] 403 test passes
- [ ] Invalid language test passes
- [ ] Test data created
- [ ] Tests run successfully

---

### Prompt 6.5: Manual QA Testing

**Objective**: Perform manual QA testing on web and mobile.

**Steps**:

1. **Web Testing**
   - Login as parent
   - Navigate to invoice list
   - Click on an invoice
   - Click "Download PDF" (French)
   - Verify PDF downloads with correct data
   - Verify banking details shown
   - Verify TVA breakdown correct
   - Test Arabic language option
   - Test receipt download
   - Test with invoice that has sibling discount
   - Test error handling

2. **Mobile Testing**
   - Login as parent
   - Navigate to invoice screen
   - Click on an invoice
   - Tap "Download PDF" (French)
   - Verify PDF saves to device
   - Open PDF and verify content
   - Test Arabic language option
   - Test receipt download
   - Test with large invoice (many items)
   - Test error handling

**Checklist**:

- [ ] Web: Login successful
- [ ] Web: Invoice PDF download (French)
- [ ] Web: Banking details shown
- [ ] Web: TVA breakdown correct
- [ ] Web: Arabic language works
- [ ] Web: Receipt download works
- [ ] Web: Sibling discount shown
- [ ] Web: Error handling works
- [ ] Mobile: Login successful
- [ ] Mobile: Invoice PDF saves (French)
- [ ] Mobile: PDF content correct
- [ ] Mobile: Arabic language works
- [ ] Mobile: Receipt download works
- [ ] Mobile: Large invoice works
- [ ] Mobile: Error handling works

---

## Phase 7: Deployment

### Prompt 7.1: Run Database Migration

**Objective**: Apply database migration to production.

**Steps**:

1. **Backup database**
   - Create database backup before migration

2. **Test migration locally**
   - Run `alembic upgrade head` on staging
   - Verify no errors
   - Run `alembic downgrade -1` to test rollback

3. **Apply to production**
   - Run `alembic upgrade head` on production
   - Verify migration success
   - Check database schema

4. **Verify data**
   - Check schools table has new columns
   - Check invoice_items table has new columns
   - Verify all columns are nullable

**Checklist**:

- [ ] Database backup created
- [ ] Migration tested on staging
- [ ] Staging migration successful
- [ ] Staging rollback tested
- [ ] Production migration executed
- [ ] Production migration successful
- [ ] Schools columns verified
- [ ] Invoice_items columns verified
- [ ] Columns nullable verified

---

### Prompt 7.2: Deploy Backend Code

**Objective**: Deploy backend code with new features.

**Steps**:

1. **Build Docker image**
   - Build backend Docker image with new code
   - Tag with version number

2. **Push to registry**
   - Push Docker image to container registry

3. **Deploy to Kubernetes**
   - Update Helm chart with new image tag
   - Run `helm upgrade`
   - Verify pods are running

4. **Verify deployment**
   - Check backend logs
   - Check health endpoints
   - Verify ARQ worker running

**Checklist**:

- [ ] Docker image built
- [ ] Image tagged correctly
- [ ] Image pushed to registry
- [ ] Helm chart updated
- [ ] Helm upgrade executed
- [ ] Pods running
- [ ] Backend logs clean
- [ ] Health endpoints responding
- [ ] ARQ worker running

---

### Prompt 7.3: Deploy Frontend Code

**Objective**: Deploy web and mobile frontend code with new features.

**Steps**:

1. **Web Deployment**
   - Build React application
   - Deploy to hosting
   - Verify new buttons appear

2. **Mobile Deployment**
   - Build Flutter application
   - Submit to app stores (or deploy to test flight)
   - Verify new buttons appear

3. **Verify integration**
   - Test web download flow
   - Test mobile download flow
   - Verify API communication

**Checklist**:

- [ ] Web app built
- [ ] Web app deployed
- [ ] Web buttons appear
- [ ] Mobile app built
- [ ] Mobile app deployed
- [ ] Mobile buttons appear
- [ ] Web download flow works
- [ ] Mobile download flow works
- [ ] API communication verified

---

### Prompt 7.4: Post-Deployment Monitoring

**Objective**: Monitor system after deployment.

**Steps**:

1. **Check metrics**
   - Monitor report generation duration
   - Monitor report generation success rate
   - Monitor error rates

2. **Check logs**
   - Review backend logs for errors
   - Review ARQ worker logs
   - Review MinIO logs

3. **Check storage**
   - Monitor MinIO storage usage
   - Verify PDFs being stored
   - Verify cleanup job running

4. **User feedback**
   - Monitor support tickets
   - Gather user feedback
   - Address any issues

**Checklist**:

- [ ] Report generation duration monitored
- [ ] Success rate monitored
- [ ] Error rates monitored
- [ ] Backend logs reviewed
- [ ] ARQ worker logs reviewed
- [ ] MinIO logs reviewed
- [ ] Storage usage monitored
- [ ] PDF storage verified
- [ ] Cleanup job verified
- [ ] Support tickets monitored
- [ ] User feedback gathered

---

## Summary

This implementation guide breaks down the payment documentation features into:

- **7 Phases** - Grouping related work together
- **24 Prompts** - Specific tasks to complete
- **Detailed Steps** - Substeps for each prompt
- **Checklists** - Dynamic detailed todos for verification

All prompts leverage existing infrastructure (ReportsService, ARQ worker, MinIO) to minimize coding effort and ensure consistency with the existing system.
