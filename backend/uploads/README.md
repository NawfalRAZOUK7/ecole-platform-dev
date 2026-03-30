# uploads/ — File Storage

User-uploaded files including course content and student submissions. Organized by content type.

## Directory Structure

```
uploads/
├── content/           # Course materials
│   ├── courses/       # Course documents, videos, PDFs
│   ├── images/        # Course images
│   ├── attachments/   # General files
│   └── videos/        # Video content
│
└── submissions/       # Student submissions
    ├── assignments/   # Assignment files
    ├── projects/      # Project deliverables
    └── exams/         # Exam papers
```

## Storage Paths

### content/ — Course Materials

Files uploaded by teachers and admins:

```
uploads/content/{course_id}/
├── syllabus.pdf
├── materials/
│   ├── chapter-1-intro.pdf
│   ├── chapter-2-methods.pdf
│   └── resources.zip
├── images/
│   ├── diagram-1.png
│   └── diagram-2.png
└── videos/
    ├── lecture-1.mp4
    └── lecture-2.mp4
```

**Permissions:** Teacher (upload) → Students (read)

### submissions/ — Student Work

Files uploaded by students:

```
uploads/submissions/{assignment_id}/
├── student_{user_id}/
│   ├── submission.pdf
│   ├── essay.docx
│   └── code.zip
└── student_{user_id2}/
    ├── submission.pdf
    └── supporting-docs/
        ├── references.txt
        └── images.zip
```

**Permissions:** Student (upload own) → Teacher (read all)

## File Management

### Upload Service

The `FileStorageService` handles:
- File validation (size, type, content)
- Virus scanning (ClamAV integration)
- Storage abstraction (local filesystem or S3)
- Metadata tracking
- Access logging

```python
class FileStorageService:
    """Manage file uploads and downloads."""

    async def upload_file(
        self,
        file: UploadFile,
        user_id: int,
        category: str,  # "course_material", "assignment_submission"
        metadata: dict
    ) -> FileRecord:
        """Upload file with validation."""
        # Validate file size
        if file.size > MAX_FILE_SIZE:
            raise FileTooLargeError()

        # Validate MIME type
        if file.content_type not in ALLOWED_TYPES:
            raise InvalidFileTypeError()

        # Scan for viruses
        await self.scan_for_viruses(file)

        # Store file
        file_path = await self.storage_backend.save(file)

        # Create metadata record
        record = FileRecord(
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            category=category,
            metadata=metadata
        )
        await self.repo.create(record)

        # Log access
        await self.audit_log(user_id, "file_upload", file_path)

        return record

    async def download_file(
        self,
        file_id: int,
        user_id: int
    ) -> FileResponse:
        """Download file with permission check."""
        record = await self.repo.get(file_id)

        # Verify user can access
        if not await self.check_permission(user_id, record):
            raise PermissionDeniedError()

        # Log access
        await self.audit_log(user_id, "file_download", record.file_path)

        # Return file
        return FileResponse(
            path=record.file_path,
            filename=record.filename
        )
```

## Storage Backend

### Local Filesystem (Development)

```python
class LocalStorageBackend:
    """Store files on local disk."""

    async def save(self, file: UploadFile, category: str) -> str:
        """Save file and return path."""
        # Create directory
        dir_path = f"uploads/{category}/"
        os.makedirs(dir_path, exist_ok=True)

        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid4()}{ext}"
        file_path = f"{dir_path}{filename}"

        # Write to disk
        with open(file_path, 'wb') as f:
            f.write(await file.read())

        return file_path

    async def delete(self, file_path: str) -> None:
        """Delete file."""
        os.remove(file_path)
```

### AWS S3 (Production)

```python
class S3StorageBackend:
    """Store files in AWS S3."""

    async def save(self, file: UploadFile, category: str) -> str:
        """Upload to S3."""
        key = f"{category}/{uuid4()}"

        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=await file.read(),
            ContentType=file.content_type
        )

        return f"s3://{self.bucket_name}/{key}"

    async def delete(self, file_path: str) -> None:
        """Delete from S3."""
        key = file_path.replace(f"s3://{self.bucket_name}/", "")
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=key
        )
```

## File Limits

### Size Constraints

| Type | Limit | Notes |
|------|-------|-------|
| Single file | 100 MB | PDF, video, etc. |
| Total per user/month | 5 GB | Storage quota |
| Course materials | 1 GB per course | Teacher limit |
| Assignment submissions | 50 MB per submission | Student limit |

### Type Whitelist

Allowed file types:

```
Documents: PDF, DOCX, XLSX, PPTX, TXT
Images: PNG, JPG, GIF, SVG
Archives: ZIP, RAR, 7Z
Video: MP4, MOV, AVI, MKV
Audio: MP3, WAV, M4A
Code: PY, JS, JAVA, CPP, TXT
```

Blocked: EXE, BAT, SH, DLL (executables)

## Virus Scanning

Integration with ClamAV:

```python
class VirusScanner:
    """Scan files for malware."""

    async def scan(self, file_path: str) -> bool:
        """Scan file, return True if safe."""
        proc = await asyncio.create_subprocess_exec(
            'clamscan',
            '--no-summary',
            file_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, _ = await proc.communicate()

        if proc.returncode == 0:
            return True  # Clean
        elif proc.returncode == 1:
            raise VirusDetectedError()  # Infected
        else:
            raise ScanError()  # Scanner error
```

## Access Control

File downloads are permission-checked:

```python
async def check_permission(
    user_id: int,
    file_record: FileRecord
) -> bool:
    """Verify user can download file."""

    user = await get_current_user(user_id)

    # Course materials: enrolled students + teacher
    if file_record.category == "course_material":
        course = await get_course(file_record.course_id)
        if user.id == course.teacher_id:
            return True  # Teacher
        enrollment = await check_enrollment(user_id, course.id)
        return enrollment is not None  # Student

    # Assignment submissions: student + grader
    if file_record.category == "assignment_submission":
        submission = await get_submission(file_record.submission_id)
        if user.id == submission.student_id:
            return True  # Own submission
        assignment = await get_assignment(submission.assignment_id)
        course = await get_course(assignment.course_id)
        return user.id == course.teacher_id  # Teacher

    # School admin can access all
    if has_permission(user, "PERM-IAM:file:admin"):
        return True

    return False
```

## Cleanup

Automatic cleanup of old/deleted files:

```python
class FileCleanupService:
    """Remove orphaned files."""

    async def cleanup_old_files(self, days: int = 30):
        """Delete unreferenced files older than N days."""
        cutoff = datetime.now() - timedelta(days=days)

        # Find deleted file records
        deleted = await repo.get_deleted_files(before=cutoff)

        for file_record in deleted:
            await self.storage.delete(file_record.file_path)
            await repo.hard_delete(file_record.id)

    async def cleanup_student_files(self, user_id: int):
        """Delete all files for graduating student (GDPR)."""
        files = await repo.get_user_files(user_id)

        for file_record in files:
            await self.storage.delete(file_record.file_path)
            await repo.hard_delete(file_record.id)
```

## Monitoring

File storage metrics:

```python
class FileStorageMetrics:
    """Track storage usage."""

    async def get_school_storage_usage(self, school_id: int) -> dict:
        """Get storage stats for school."""
        files = await repo.get_school_files(school_id)

        total_size = sum(f.file_size for f in files)
        total_files = len(files)
        by_type = {}

        for file in files:
            ext = os.path.splitext(file.filename)[1]
            by_type[ext] = by_type.get(ext, 0) + file.file_size

        return {
            "total_size_mb": total_size / (1024 * 1024),
            "total_files": total_files,
            "usage_percentage": (total_size / SCHOOL_QUOTA) * 100,
            "by_type": by_type
        }

    async def get_quota_exceeded_schools(self) -> list[int]:
        """Get schools over quota."""
        schools = await repo.get_all_schools()
        exceeded = []

        for school in schools:
            usage = await self.get_school_storage_usage(school.id)
            if usage["usage_percentage"] > 100:
                exceeded.append(school.id)

        return exceeded
```

## API Endpoints

### Upload File

```
POST /documents
Content-Type: multipart/form-data

Form data:
- file: <binary>
- document_type: "course_material"
- title: "Lecture notes"

Response: {
  "id": 123,
  "filename": "lecture-notes.pdf",
  "file_size": 2048576,
  "download_url": "/documents/123/download"
}
```

### Download File

```
GET /documents/{file_id}/download

Response: <binary file content>
Headers:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename="lecture-notes.pdf"
```

### List User Files

```
GET /documents?category=course_material

Response: {
  "items": [
    {
      "id": 1,
      "filename": "notes.pdf",
      "file_size": 1024000,
      "created_at": "2024-03-15T10:00:00Z"
    }
  ],
  "total": 15
}
```

## Configuration

File storage settings in `core/config.py`:

```python
# File storage
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
SCHOOL_STORAGE_QUOTA = 5 * 1024 * 1024 * 1024  # 5 GB
STORAGE_BACKEND = "local"  # "local" or "s3"

# Local storage
UPLOADS_DIR = "uploads"

# AWS S3
S3_BUCKET = "ecole-platform-uploads"
S3_REGION = "eu-west-1"
S3_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Virus scanning
ENABLE_VIRUS_SCAN = True
CLAMSCAN_PATH = "/usr/bin/clamscan"

# Allowed file types
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
```

## Deployment

### Development

Files stored locally in `uploads/` directory (git-ignored).

### Production

Files stored in AWS S3 with:
- Server-side encryption
- CloudFront CDN distribution
- Lifecycle policies (archive old files)
- Versioning enabled
- Access logs

## Next Steps

- See `services/file_storage.py` for implementation
- See `api/v1/documents.py` for API endpoints
- See `models/documents.py` for database schema
