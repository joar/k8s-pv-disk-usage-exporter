FROM python:3.6-slim

WORKDIR /app

COPY requirements.txt /app/
RUN apt-get update \
    && apt-get install \
        --yes \
        --no-install-recommends \
        gcc \
        libc6-dev \
        linux-libc-dev \
    && pip install -r requirements.txt \
    && apt-get remove --purge --yes \
        gcc \
        linux-libc-dev \
    && apt-get autoremove --purge --yes

COPY disk_usage_exporter.py LICENSE /app/

ENTRYPOINT ["python", "disk_usage_exporter.py"]
