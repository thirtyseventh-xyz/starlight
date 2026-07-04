FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim

WORKDIR /usr/src/starlight

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8135", "app:app"]
STOPSIGNAL SIGINT