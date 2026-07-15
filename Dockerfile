FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim

WORKDIR /usr/src/starlight

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

CMD ["sh", "-c", "uv run alembic upgrade head && exec .venv/bin/python entrypoint.py"]
STOPSIGNAL SIGINT