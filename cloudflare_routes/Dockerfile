ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    curl \
    jq

RUN pip3 install --break-system-packages \
    flask \
    requests \
    pyyaml \
    werkzeug

RUN mkdir -p /app/templates

COPY app/ /app/
COPY run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /app
CMD ["/run.sh"]
