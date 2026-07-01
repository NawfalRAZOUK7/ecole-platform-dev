# ClamAV Setup Guide

This project already exposes a virus-scan hook in `backend/app/services/file_storage.py`.
To enable it, run a ClamAV daemon and set the backend environment variables below.

## 1. Start ClamAV

Example with Docker:

```bash
docker run --rm \
  --name ecole-clamav \
  -p 3310:3310 \
  clamav/clamav:stable
```

Wait until `clamd` finishes its initial signature update and starts listening on port `3310`.

## 2. Configure the backend

Set these values in your backend environment:

```env
VIRUS_SCAN_ENABLED=true
VIRUS_SCAN_HOST=localhost
VIRUS_SCAN_PORT=3310
```

These map directly to:

- `virus_scan_enabled`
- `virus_scan_host`
- `virus_scan_port`

in `backend/app/core/config.py`.

## 3. Verify

1. Start the backend with virus scanning enabled.
2. Upload a normal PDF or image and confirm the upload succeeds.
3. Upload an EICAR test file and confirm the backend rejects it with a document validation error.

## Notes

- The current implementation uses ClamAV `INSTREAM` scanning.
- If ClamAV is unavailable while scanning is enabled, uploads fail closed.
- Keep ClamAV signature updates enabled in any shared or production environment.
