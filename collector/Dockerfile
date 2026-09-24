FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    COLLECTOR_DIR=/collector \
    TZ=UTC

WORKDIR /collector

# tzdata: OS-level zone database, overridden at runtime via the TZ
# environment variable (see deployment/docker-compose.yml / .env.example).
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
        dmidecode \
        util-linux \
        curl \
        tzdata \
        vim \
        less \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# No ansible-galaxy collection install needed: ansible.cfg's YAML output
# (stdout_callback = default, callback_result_format = yaml) is a
# built-in ansible-core option, not a collection-provided callback - see
# the comment in ansible.cfg for why that matters.

EXPOSE 9100

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9100/health || exit 1

CMD ["uvicorn", "agent:app", "--host", "0.0.0.0", "--port", "9100"]
