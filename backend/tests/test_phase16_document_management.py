"""Phase 16 document management coverage.

Integration tests run against the Docker-backed backend + postgres + redis stack.
Seed data must be loaded before execution (make seed).

Run:
  python -m pytest tests/test_phase16_document_management.py -v
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from app.core.database import async_session
from app.models.documents import Document
from app.services.file_storage import LocalFileStorageBackend, S3FileStorageBackend


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF"
    )


def _sample_png_bytes() -> bytes:
    return bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000A49444154789C6360000002000154A24F5D0000000049454E44AE426082"
    )


def _sample_zip_bytes() -> bytes:
    return b"PK\x03\x04phase16 zip payload"


async def _parent_student_id(client: httpx.AsyncClient, token: str) -> str:
    response = await client.get(
        "/documents/options",
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    students = response.json()["data"]["students"]
    assert students, "Expected at least one linked student for the parent seed user"
    return students[0]["id"]


async def _upload_document(
    client: httpx.AsyncClient,
    token: str,
    *,
    filename: str,
    content: bytes,
    mime_type: str,
    category: str = "other",
    linked_student_id: str | None = None,
) -> dict:
    response = await client.post(
        "/documents/upload",
        headers=_auth_headers(token),
        data={
            "category": category,
            **(
                {"linked_student_id": linked_student_id}
                if linked_student_id is not None
                else {}
            ),
        },
        files={"file": (filename, content, mime_type)},
    )
    assert response.status_code in {200, 201}, response.text
    return response.json()["data"]


async def _upload_resource(
    client: httpx.AsyncClient,
    token: str,
    *,
    filename: str,
    content: bytes,
    mime_type: str,
    title: str,
    subject: str = "Mathematics",
    level: str = "College",
    resource_type: str = "worksheet",
) -> dict:
    response = await client.post(
        "/resources",
        headers=_auth_headers(token),
        data={
            "title": title,
            "subject": subject,
            "level": level,
            "type": resource_type,
            "visibility": "school",
            "tags": "phase16,documents",
        },
        files={"file": (filename, content, mime_type)},
    )
    assert response.status_code in {200, 201}, response.text
    return response.json()["data"]


class TestDocumentManagementIntegration:
    @pytest.mark.asyncio
    async def test_upload_download_preview_and_allowed_mime_types(
        self,
        client: httpx.AsyncClient,
        parent_token: str,
        admin_token: str,
    ):
        uploads: list[dict] = []
        samples = [
            ("phase16.pdf", _sample_pdf_bytes(), "application/pdf"),
            (
                "phase16.docx",
                _sample_zip_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
            (
                "phase16.xlsx",
                _sample_zip_bytes(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            (
                "phase16.pptx",
                _sample_zip_bytes(),
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ),
            ("phase16.png", _sample_png_bytes(), "image/png"),
            ("phase16.webp", _sample_png_bytes(), "image/webp"),
            ("phase16.zip", _sample_zip_bytes(), "application/zip"),
        ]

        try:
            for filename, content, mime_type in samples:
                uploaded = await _upload_document(
                    client,
                    parent_token,
                    filename=f"{uuid.uuid4()}-{filename}",
                    content=content,
                    mime_type=mime_type,
                )
                uploads.append(uploaded)

            list_response = await client.get(
                "/documents",
                headers=_auth_headers(parent_token),
                params={"owner": "me", "limit": 100},
            )
            assert list_response.status_code == 200
            listed_ids = {item["id"] for item in list_response.json()["data"]}
            assert {item["id"] for item in uploads}.issubset(listed_ids)

            pdf_document = next(
                item for item in uploads if item["mime_type"] == "application/pdf"
            )
            pdf_download = await client.get(
                pdf_document["download_url"].replace(
                    "http://localhost:8000/api/v1", ""
                ),
            )
            assert pdf_download.status_code == 200
            assert pdf_download.content.startswith(b"%PDF")

            image_document = next(
                item for item in uploads if item["mime_type"] == "image/png"
            )
            preview = await client.get(
                image_document["preview_url"].replace(
                    "http://localhost:8000/api/v1", ""
                ),
            )
            assert preview.status_code == 200
            assert preview.headers["content-type"].startswith("image/")
        finally:
            for uploaded in uploads:
                await client.delete(
                    f"/documents/{uploaded['id']}?hard=true",
                    headers=_auth_headers(admin_token),
                )

    @pytest.mark.asyncio
    async def test_sha256_dedup_and_student_checklist(
        self,
        client: httpx.AsyncClient,
        parent_token: str,
        admin_token: str,
    ):
        student_id = await _parent_student_id(client, parent_token)
        first = await _upload_document(
            client,
            parent_token,
            filename=f"{uuid.uuid4()}-medical.pdf",
            content=_sample_pdf_bytes(),
            mime_type="application/pdf",
            category="medical",
            linked_student_id=student_id,
        )
        second = await _upload_document(
            client,
            parent_token,
            filename=f"{uuid.uuid4()}-medical.pdf",
            content=_sample_pdf_bytes(),
            mime_type="application/pdf",
            category="medical",
            linked_student_id=student_id,
        )

        try:
            assert second["deduplicated"] is True
            assert first["sha256"] == second["sha256"]

            async with async_session() as session:
                documents = (
                    (
                        await session.execute(
                            select(Document)
                            .where(
                                Document.id.in_(
                                    [uuid.UUID(first["id"]), uuid.UUID(second["id"])]
                                )
                            )
                            .order_by(Document.created_at.asc())
                        )
                    )
                    .scalars()
                    .all()
                )
                assert len(documents) == 2
                assert documents[0].storage_path == documents[1].storage_path

            checklist_response = await client.get(
                f"/students/{student_id}/documents/checklist",
                headers=_auth_headers(parent_token),
            )
            assert checklist_response.status_code == 200
            checklist = checklist_response.json()["data"]
            medical_item = next(
                item for item in checklist if item["category"] == "medical"
            )
            assert medical_item["status"] == "uploaded"
            assert medical_item["document"]["id"] in {first["id"], second["id"]}
        finally:
            await client.delete(
                f"/documents/{first['id']}?hard=true",
                headers=_auth_headers(admin_token),
            )
            await client.delete(
                f"/documents/{second['id']}?hard=true",
                headers=_auth_headers(admin_token),
            )

    @pytest.mark.asyncio
    async def test_resource_search_rating_and_rbac(
        self,
        client: httpx.AsyncClient,
        teacher_token: str,
        student_token: str,
        admin_token: str,
    ):
        title = f"Phase16 worksheet {uuid.uuid4()}"
        resource = await _upload_resource(
            client,
            teacher_token,
            filename=f"{uuid.uuid4()}-worksheet.pdf",
            content=_sample_pdf_bytes(),
            mime_type="application/pdf",
            title=title,
        )

        try:
            token_download = await client.get(
                resource["download_url"].replace("http://localhost:8000/api/v1", "")
            )
            assert token_download.status_code == 200
            assert token_download.headers["content-type"].startswith("application/pdf")
            assert token_download.content.startswith(b"%PDF")

            search_response = await client.get(
                "/resources",
                headers=_auth_headers(teacher_token),
                params={
                    "q": title.split()[-1],
                    "subject": "Mathematics",
                    "type": "worksheet",
                },
            )
            assert search_response.status_code == 200
            assert any(
                item["id"] == resource["id"] for item in search_response.json()["data"]
            )

            rate_response = await client.post(
                f"/resources/{resource['id']}/rate",
                headers=_auth_headers(teacher_token),
                json={"rating": 5},
            )
            assert rate_response.status_code == 200
            assert rate_response.json()["data"]["avg_rating"] == pytest.approx(5.0)

            rating_response = await client.get(
                f"/resources/{resource['id']}/rating",
                headers=_auth_headers(teacher_token),
            )
            assert rating_response.status_code == 200
            assert rating_response.json()["data"]["my_rating"] == 5

            unauthenticated = await client.post(
                "/resources",
                data={
                    "title": "No auth",
                    "type": "worksheet",
                    "visibility": "school",
                },
                files={"file": ("no-auth.pdf", _sample_pdf_bytes(), "application/pdf")},
            )
            assert unauthenticated.status_code == 401

            forbidden = await client.post(
                "/resources",
                headers=_auth_headers(student_token),
                data={
                    "title": "Forbidden",
                    "type": "worksheet",
                    "visibility": "school",
                },
                files={
                    "file": ("forbidden.pdf", _sample_pdf_bytes(), "application/pdf")
                },
            )
            assert forbidden.status_code == 403
        finally:
            await client.delete(
                f"/resources/{resource['id']}",
                headers=_auth_headers(admin_token),
            )

    @pytest.mark.asyncio
    async def test_document_deny_ordering_and_hidden_visibility(
        self,
        client: httpx.AsyncClient,
        parent_token: str,
        student_token: str,
        admin_token: str,
    ):
        unauthenticated = await client.get("/documents")
        assert unauthenticated.status_code == 401

        forbidden = await client.post(
            "/documents/upload",
            headers=_auth_headers(student_token),
            data={"category": "other"},
            files={"file": ("student.pdf", _sample_pdf_bytes(), "application/pdf")},
        )
        assert forbidden.status_code == 403

        hidden = await _upload_document(
            client,
            parent_token,
            filename=f"{uuid.uuid4()}-hidden.pdf",
            content=_sample_pdf_bytes(),
            mime_type="application/pdf",
        )

        try:
            masked = await client.get(
                f"/documents/{hidden['id']}",
                headers=_auth_headers(student_token),
            )
            assert masked.status_code == 404

            delete_masked = await client.delete(
                f"/documents/{hidden['id']}",
                headers=_auth_headers(student_token),
            )
            assert delete_masked.status_code == 404
        finally:
            await client.delete(
                f"/documents/{hidden['id']}?hard=true",
                headers=_auth_headers(admin_token),
            )


class TestDocumentStorageBackends:
    @pytest.mark.asyncio
    async def test_local_storage_backend_round_trip(self, tmp_path: Path):
        backend = LocalFileStorageBackend(base_dir=str(tmp_path))
        payload = b"phase16-local-storage"

        stored = await backend.save_bytes(
            relative_path="phase16/test.bin",
            content=payload,
            mime_type="application/octet-stream",
        )
        assert stored.size_bytes == len(payload)
        assert await backend.exists("phase16/test.bin") is True

        local_path = await backend.local_path("phase16/test.bin")
        assert local_path.read_bytes() == payload

        await backend.delete("phase16/test.bin")
        assert await backend.exists("phase16/test.bin") is False

    @pytest.mark.asyncio
    async def test_s3_storage_backend_with_mock_client(self, tmp_path: Path):
        class _FakeS3Client:
            def __init__(self) -> None:
                self.objects: dict[tuple[str, str], bytes] = {}

            def put_object(
                self, *, Bucket: str, Key: str, Body: bytes, ContentType: str
            ):
                self.objects[(Bucket, Key)] = Body

            def head_object(self, *, Bucket: str, Key: str):
                if (Bucket, Key) not in self.objects:
                    raise FileNotFoundError(Key)
                return {"ContentLength": len(self.objects[(Bucket, Key)])}

            def delete_object(self, *, Bucket: str, Key: str):
                self.objects.pop((Bucket, Key), None)

            def download_fileobj(
                self, bucket: str, key: str, handle: io.BufferedWriter
            ):
                handle.write(self.objects[(bucket, key)])

        backend = S3FileStorageBackend(client=_FakeS3Client())
        backend.bucket = "phase16-documents"
        payload = b"phase16-s3-storage"

        stored = await backend.save_bytes(
            relative_path="phase16/s3.bin",
            content=payload,
            mime_type="application/octet-stream",
        )
        assert stored.size_bytes == len(payload)
        assert await backend.exists("phase16/s3.bin") is True

        local_path = await backend.local_path("phase16/s3.bin")
        assert local_path.read_bytes() == payload

        await backend.delete("phase16/s3.bin")
        assert await backend.exists("phase16/s3.bin") is False
