FROM python:3.12-slim

LABEL org.opencontainers.image.title="MEDIA Security Audit Platform"
LABEL org.opencontainers.image.description="Local MSP security audit platform for authorized, non-destructive assessments"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

ARG APP_UID=10001
ARG APP_GID=10001

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        nmap \
        smbclient \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${APP_GID}" mediaaudit \
    && useradd --uid "${APP_UID}" --gid mediaaudit --create-home --shell /usr/sbin/nologin mediaaudit

WORKDIR /opt/media-security-audit

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --upgrade pip \
    && python -m pip install .

RUN mkdir -p \
        /var/lib/media-audit/data \
        /var/lib/media-audit/runs \
        /var/lib/media-audit/reports \
        /var/lib/media-audit/evidence \
    && chown -R mediaaudit:mediaaudit /var/lib/media-audit

USER mediaaudit

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=3).read()"

CMD ["media-audit", "web", "--data-dir", "/var/lib/media-audit/data", "--reports-dir", "/var/lib/media-audit/reports", "--host", "0.0.0.0", "--port", "8080"]
