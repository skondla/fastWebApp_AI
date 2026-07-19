FROM python:3.11-slim
LABEL maintainer="Sudheer Kondla, skondla@me.com"
LABEL description="FastAPI DB Restore Management Tool with JWT OAuth 2.0"

# ── System setup ───────────────────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssl \
        curl \
        mailutils && \
    rm -rf /var/lib/apt/lists/*

# ── Non-root user ─────────────────────────────────────────────────────────────
RUN groupadd -r app && \
    useradd -r -g app -d /home/app -s /sbin/nologin -c "Docker image user" app

# ── App directory ─────────────────────────────────────────────────────────────
WORKDIR /app
COPY . /app

# ── SSL/TLS self-signed certificate ───────────────────────────────────────────
RUN mkdir -p /app/certs && \
    openssl genrsa -des3 -passout pass:x -out /tmp/server.pass.key 2048 && \
    openssl rsa -passin pass:x -in /tmp/server.pass.key -out /app/certs/key.pem && \
    rm /tmp/server.pass.key && \
    openssl req -new -key /app/certs/key.pem -out /tmp/server.csr \
        -subj "/C=US/ST=GA/L=Atlanta/O=Data Cube Inc/OU=IT Department/CN=www.datacubeinc.com" && \
    openssl x509 -req -days 365 -in /tmp/server.csr \
        -signkey /app/certs/key.pem -out /app/certs/certificate.pem && \
    rm /tmp/server.csr

# ── Python dependencies ────────────────────────────────────────────────────────
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# ── Place lib modules on PYTHONPATH ───────────────────────────────────────────
RUN cp lib/*.py /usr/local/lib/python3.11/

# ── Permissions ───────────────────────────────────────────────────────────────
RUN chmod +x startup.sh && \
    chown -R app:app /app

USER app

# ── Ports ─────────────────────────────────────────────────────────────────────
EXPOSE 50443
EXPOSE 8000

ENTRYPOINT ["/bin/bash"]
CMD ["startup.sh"]
