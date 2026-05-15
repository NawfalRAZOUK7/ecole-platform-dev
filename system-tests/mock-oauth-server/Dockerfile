FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn python-jose[cryptography] pydantic

COPY main.py .
COPY fixtures/ ./fixtures/

EXPOSE 9999

CMD ["python", "main.py"]
