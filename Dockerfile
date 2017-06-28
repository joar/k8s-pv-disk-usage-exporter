FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt /app/
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        libc-dev \
        linux-headers \
    && pip install -r requirements.txt \
    && apk del .build-deps

COPY  LICENSE /app/
COPY ./disk_usage_exporter /app/disk_usage_exporter
ENV PYTHONPATH=/app/

ENTRYPOINT ["python", "-m", "disk_usage_exporter"]
