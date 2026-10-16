FROM python:3.12-slim

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
COPY apps/api/src ./apps/api/src
RUN pip install --no-cache-dir .
USER app
EXPOSE 8080 8090
CMD ["uvicorn", "agentconstruct.main:app", "--host", "0.0.0.0", "--port", "8080"]
