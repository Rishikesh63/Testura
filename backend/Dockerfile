FROM python:3.11-slim

WORKDIR /app

# Install git, Node.js, npm
RUN apt-get update && apt-get install -y git curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install jest globally
RUN npm install -g jest

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./
RUN poetry install --only main --no-interaction --no-ansi

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
