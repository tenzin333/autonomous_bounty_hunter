# Use a lightweight Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Semgrep and project requirements
RUN pip install semgrep openai python-dotenv

WORKDIR /app
COPY . .

# Entry point for the Fargate Task
CMD ["python", "main.py"]