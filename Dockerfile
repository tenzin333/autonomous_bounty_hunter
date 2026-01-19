# Use Python 3.12 slim for a small footprint
FROM python:3.12-slim

# Install system dependencies for Foundry, Psycopg2, and Flask
RUN apt-get update && apt-get install -y \
    curl git libpq-dev gcc procps && \
    rm -rf /var/lib/apt/lists/*

# Install Foundry (Forge/Anvil)
RUN curl -L https://foundry.paradigm.xyz | bash && \
    /root/.foundry/bin/foundryup
ENV PATH="/root/.foundry/bin:${PATH}"

WORKDIR /app
# This line fixes the ModuleNotFoundError for all scripts
ENV PYTHONPATH="/app"

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Render expects the service to listen on a port
EXPOSE 10000

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]