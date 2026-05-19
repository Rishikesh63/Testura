FROM python:3.12-slim

# Install Node.js and test runners
RUN apt-get update && \
    apt-get install -y nodejs npm git --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pytest pytest-json-report pytest-timeout
RUN npm install -g jest

# Create non-root sandbox user — never run tests as root
RUN useradd -m -u 1001 sandbox
USER sandbox
WORKDIR /sandbox

# No network, no privilege escalation enforced at runtime via docker run flags:
# --network none --memory 512m --cpus 1 --read-only (except /sandbox)
