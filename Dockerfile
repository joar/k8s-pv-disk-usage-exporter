FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt /app/

# Pre-install requirements
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        libc-dev \
        linux-headers \
    && pip install -r requirements.txt \
    && apk del .build-deps

# Add application code
COPY  setup.py LICENSE README.rst /app/
COPY ./disk_usage_exporter /app/disk_usage_exporter

# Install application package
RUN python setup.py install

CMD ["disk-usage-exporter"]
