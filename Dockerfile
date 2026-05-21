FROM python:3

WORKDIR /usr/src/starlight

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8135", "app:app"]
STOPSIGNAL SIGINT