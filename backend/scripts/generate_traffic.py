"""Generate traffic against the local backend to populate Prometheus/Grafana."""

import asyncio
import random
import uuid

import httpx

BASE_URL = "http://localhost:8000/api/v1"

EMAILS = [
    "admin@ecole-benani.ma",
    "prof.math@ecole-benani.ma",
    "parent.alaoui@gmail.com",
    "yassine.alaoui@ecole-benani.ma",
]
PASSWORDS = {
    "admin@ecole-benani.ma": "admin123",
    "prof.math@ecole-benani.ma": "teacher123",
    "parent.alaoui@gmail.com": "parent123",
    "yassine.alaoui@ecole-benani.ma": "student123",
}

SCHOOL_ID = "00000000-0000-4000-8000-000000000001"

AUTH_ENDPOINTS = [
    ("GET", "/analytics/overview", {"from": "2025-01-01", "to": "2025-12-31", "compare": "false"}),
    ("GET", "/calendar/events", {"from": "2025-01-01", "to": "2025-12-31"}),
    ("GET", "/documents", {}),
    ("GET", "/invoices", {}),
    ("GET", "/students", {}),
    ("GET", "/classes", {}),
    ("GET", "/courses", {}),
    ("GET", "/assignments", {}),
    ("GET", "/grades", {}),
    ("GET", "/notifications", {}),
    ("GET", "/levels", {}),
    ("GET", "/programs", {}),
    ("GET", "/reports", {}),
    ("POST", "/calendar/events", {
        "title_fr": "Meeting",
        "type": "meeting",
        "visibility": "school",
        "start_at": "2025-12-01T09:00:00Z",
        "end_at": "2025-12-01T10:00:00Z",
        "reminder_offsets_minutes": [60],
    }),
]

PUBLIC_ENDPOINTS = [
    "/health",
    "/docs",
    "/openapi.json",
]


async def login(client: httpx.AsyncClient, email: str) -> str:
    resp = await client.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": email,
            "password": PASSWORDS[email],
            "school_id": SCHOOL_ID,
        },
    )
    data = resp.json().get("data", {})
    return data.get("access_token", "")


async def generate_user_traffic(client: httpx.AsyncClient, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(30):
        method, path, params = random.choice(AUTH_ENDPOINTS)
        try:
            if method == "GET":
                await client.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=10)
            elif method == "POST":
                body = {k: (f"Test {uuid.uuid4()}" if k == "title_fr" else v) for k, v in params.items()}
                await client.post(f"{BASE_URL}{path}", headers=headers, json=body, timeout=10)
        except Exception:
            pass
        await asyncio.sleep(0.2)


async def generate_public_traffic(client: httpx.AsyncClient):
    for _ in range(20):
        path = random.choice(PUBLIC_ENDPOINTS)
        try:
            await client.get(f"{BASE_URL}{path}", timeout=5)
        except Exception:
            pass
        await asyncio.sleep(0.2)


async def main():
    async with httpx.AsyncClient() as client:
        tokens = []
        for email in EMAILS:
            try:
                token = await login(client, email)
                if token:
                    tokens.append(token)
            except Exception:
                pass

        tasks = [generate_public_traffic(client)]
        for token in tokens:
            tasks.append(generate_user_traffic(client, token))

        await asyncio.gather(*tasks)
        print("Traffic generation complete.")


if __name__ == "__main__":
    asyncio.run(main())
