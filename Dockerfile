FROM python:3

WORKDIR /usr/src/starlight

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
STOPSIGNAL SIGINT