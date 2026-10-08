FROM python:3.12-slim

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
COPY pyproject.toml ./
COPY apps/api/src ./apps/api/src
COPY apps/web ./apps/web
RUN pip install --no-cache-dir .
USER app
ENV AGENTCONSTRUCT_WEB_ROOT=/app/apps/web
EXPOSE 8080 8090
