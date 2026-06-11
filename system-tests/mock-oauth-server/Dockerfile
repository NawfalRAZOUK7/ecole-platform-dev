FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir \
        fastapi==0.115.5 \
        uvicorn==0.34.0 \
        "python-jose[cryptography]==3.3.0" \
        pydantic==2.9.2

COPY main.py .
COPY fixtures/ ./fixtures/

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 9999

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "-sf", "http://localhost:9999/.well-known/openid-configuration"]

CMD ["python", "main.py"]
