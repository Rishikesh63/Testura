# Sandbox for running user tests safely
FROM python:3.12-slim

RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*

# Install test runners
RUN pip install pytest pytest-json-report
RUN npm install -g jest

# No network access, no root in production
RUN useradd -m sandbox
USER sandbox

WORKDIR /sandbox
